import { expect, test } from 'bun:test';
import { Document, Window } from 'happy-dom';

const bundle = await Bun.build({
    entrypoints: [new URL('../../app/static/js/report-form-htmx.js', import.meta.url).pathname],
    target: 'browser', format: 'iife', write: false,
});
if (!bundle.success) throw new AggregateError(bundle.logs, 'Report bundle failed');
const source = await bundle.outputs[0].text();

function page(body) {
    const window = new Window({
        url: 'https://mantis.example/melden',
        settings: { enableJavaScriptEvaluation: true, suppressInsecureJavaScriptEnvironmentWarning: true },
    });
    // Happy DOM's window-bound Document is not HTMLDocument's superclass.
    window.Document = Document;
    // Happy DOM lacks XPath; this fixture has no inline hx-on attributes for HTMX to find.
    window.XPathEvaluator = class {
        createExpression() { return { evaluate: () => ({ iterateNext: () => null }) }; }
    };
    window.document.head.innerHTML = '<meta name="csrf-token" content="test">';
    window.document.body.dataset.coordRange = JSON.stringify({ latitude: [24.6, 60], longitude: [-20, 44.83] });
    window.document.body.innerHTML = body;
    return window;
}

const uploadMarkup = `
    <script type="application/json" id="upload-config">{"types":{"jpg":"image/jpeg"},"extensionByMime":{"image/jpeg":"jpg"},"maxBytes":12582912,"maxMb":12}</script>
    <form id="reportForm" action="/melden" data-photo-error-url="/photo-failure">
        <div class="step"><h3>Foto</h3>
            <input type="file" id="photo" name="photo">
            <div id="photo-upload-area"></div>
            <div id="dropzoneLoadingIndicator" hidden></div>
            <div id="photoPreview" class="hidden"><img id="preview-img"></div>
            <div id="error-photo"></div>
        </div>
        <div id="error-general" class="hidden"></div>
        <button type="submit" id="submit">Absenden</button>
    </form>`;

function selectPhoto(window, name) {
    const transfer = new window.DataTransfer();
    transfer.items.add(new window.File(['original photo bytes'], name, { type: 'image/jpeg' }));
    const input = window.document.getElementById('photo');
    input.files = transfer.files;
    input.dispatchEvent(new window.Event('change', { bubbles: true }));
}

function photoPage(onRequest) {
    const window = page(uploadMarkup);
    window.happyDOM.settings.enableImageFileLoading = true;
    window.happyDOM.settings.fetch.interceptor = {
        beforeAsyncRequest: async ({ request }) => {
            if (request.method === 'GET' && request.url === window.location.href) {
                return new window.Response(null, { status: 404 });
            }
            if (request.url.startsWith('blob:')) {
                const response = await fetch(request.url);
                return new window.Response(await response.arrayBuffer());
            }
            return onRequest(request);
        },
    };
    return window;
}

test('a pending diagnostic request does not block uploading the original photo', async () => {
    const diagnostic = Promise.withResolvers();
    const submission = Promise.withResolvers();
    const window = photoPage(async request => {
        if (request.url.endsWith('/photo-failure')) return diagnostic.promise;
        submission.resolve((await request.formData()).get('photo'));
        return window.Response.json({ success: false, error: 'Submission captured' });
    });
    try {
        window.eval(source);
        window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
        const previewLoaded = new Promise(resolve =>
            window.document.getElementById('preview-img').addEventListener('load', resolve, { once: true }));
        selectPhoto(window, 'photo.jpg');
        await previewLoaded;

        expect(window.document.getElementById('dropzoneLoadingIndicator').hidden).toBe(true);
        window.document.getElementById('submit').click();
        const submittedPhoto = await submission.promise;
        expect(await submittedPhoto.text()).toBe('original photo bytes');
    } finally {
        diagnostic.resolve(new window.Response(null, { status: 204 }));
        await window.happyDOM.close();
    }
});

test.each([
    ['IMG_0001', 'IMG_0001.jpg'],
    ['', 'photo.jpg'],
])('an original photo named %s is submitted with a valid extension', async (name, expectedName) => {
    let submittedPhoto;
    const window = photoPage(async request => {
        if (request.url.endsWith('/photo-failure')) return new window.Response(null, { status: 204 });
        submittedPhoto = (await request.formData()).get('photo');
        return window.Response.json({ success: false, error: 'Submission captured' });
    });
    try {
        window.eval(source);
        window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
        selectPhoto(window, name);
        await window.happyDOM.waitUntilComplete();
        window.document.getElementById('submit').click();
        await window.happyDOM.waitUntilComplete();

        expect(submittedPhoto?.name).toBe(expectedName);
    } finally {
        await window.happyDOM.close();
    }
});

test('a failed address lookup clears the previous location and allows manual entry', async () => {
    const window = page(`
        <form id="reportForm" data-ags-url="/ags">
            <div class="step"><h3>Foto</h3></div>
            <div id="map"></div>
            <input id="manual-latitude"><input id="manual-longitude">
            <input id="latitude" name="latitude"><input id="longitude" name="longitude">
            <input id="fund_city" name="fund_city" value="Berlin">
            <input id="fund_state" name="fund_state" value="Berlin">
            <input id="fund_street" name="fund_street" value="Old Street">
            <div id="error-coordinates"></div>
            <div id="hint-coordinates"></div>
        </form>`);
    try {
        window.fetch = async url => String(url).includes('nominatim')
            ? new window.Response(null, { status: 503 }) : window.Response.json({});
        window.eval(source);
        window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
        const latitude = window.document.getElementById('manual-latitude');
        latitude.value = '52.4';
        window.document.getElementById('manual-longitude').value = '13';
        latitude.dispatchEvent(new window.Event('change', { bubbles: true }));
        await window.happyDOM.waitUntilComplete();

        const data = new window.FormData(window.document.getElementById('reportForm'));
        expect(data.get('latitude')).toBe('52.400000');
        expect(data.get('longitude')).toBe('13.000000');
        expect(data.get('fund_city')).toBe('');
        expect(data.get('fund_state')).toBe('');
        expect(data.get('fund_street')).toBe('');
        expect(window.document.getElementById('fund_city').readOnly).toBe(false);
        expect(window.document.getElementById('hint-coordinates').textContent).not.toBe('');
    } finally {
        await window.happyDOM.close();
    }
});

test('an older photo read cannot replace a newer selection', async () => {
    const oldRead = Promise.withResolvers();
    let submittedPhoto;
    const window = photoPage(async request => {
        if (request.url.endsWith('/photo-failure')) return new window.Response(null, { status: 204 });
        submittedPhoto = (await request.formData()).get('photo');
        return window.Response.json({ success: false, error: 'Submission captured' });
    });
    try {
        window.eval(source);
        window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
        const oldFile = new window.File(['older photo'], 'older.jpg', { type: 'image/jpeg' });
        oldFile.arrayBuffer = () => oldRead.promise;
        const transfer = new window.DataTransfer();
        transfer.items.add(oldFile);
        const input = window.document.getElementById('photo');
        input.files = transfer.files;
        input.dispatchEvent(new window.Event('change', { bubbles: true }));
        selectPhoto(window, 'newer.jpg');
        await window.happyDOM.waitUntilComplete();
        oldRead.resolve(new TextEncoder().encode('older photo').buffer);
        await window.happyDOM.waitUntilComplete();
        window.document.getElementById('submit').click();
        await window.happyDOM.waitUntilComplete();

        expect(submittedPhoto.name).toBe('newer.jpg');
        expect(await submittedPhoto.text()).toBe('original photo bytes');
    } finally {
        oldRead.resolve(new ArrayBuffer(0));
        await window.happyDOM.close();
    }
});

test('pasting a replacement leaves the stale review and returns to the photo step', async () => {
    const window = photoPage(async request => {
        if (request.url.endsWith('/validate')) {
            const step = new URLSearchParams(await request.text()).get('step');
            return new window.Response('', {
                headers: { 'HX-Trigger': JSON.stringify({ stepValid: { nextStep: Number(step) + 1 } }) },
            });
        }
        if (request.url.endsWith('/review')) return new window.Response('<img id="review-photo">');
        return new window.Response(null, { status: 204 });
    });
    try {
        const form = window.document.getElementById('reportForm');
        form.dataset.reviewUrl = '/review';
        form.querySelector('.step').insertAdjacentHTML('beforeend', `
            <button type="button" data-step="1" hx-post="/validate" hx-vals='{"step":1}'
                hx-target="#validation-errors-container">Weiter</button>`);
        form.insertAdjacentHTML('beforeend', `
            <div id="validation-errors-container"></div>
            <div class="step"><h3>Ort</h3>
                <input id="latitude" value="52.4"><input id="longitude" value="13">
                <button type="button" data-step="2" hx-post="/validate" hx-vals='{"step":2}'
                    hx-target="#validation-errors-container">Weiter</button>
            </div>
            <div class="step"><h3>Kontakt</h3>
                <button type="button" data-step="3" hx-post="/validate" hx-vals='{"step":3}'
                    hx-target="#validation-errors-container">Weiter</button>
            </div>
            <div class="step" id="review-step"><h3>Review</h3>
                <div id="review-content-container"></div>
            </div>`);
        window.eval(source);
        window.document.dispatchEvent(new window.Event('DOMContentLoaded'));
        selectPhoto(window, 'old.jpg');
        await window.happyDOM.waitUntilComplete();
        form.querySelector('[data-step="1"]').click();
        await window.happyDOM.waitUntilComplete();
        form.querySelector('[data-step="2"]').click();
        await window.happyDOM.waitUntilComplete();
        form.querySelector('[data-step="3"]').click();
        await window.happyDOM.waitUntilComplete();
        expect(window.document.getElementById('review-step').classList.contains('hidden')).toBe(false);
        expect(window.document.getElementById('review-photo').src).toStartWith('blob:');

        const clipboard = new window.DataTransfer();
        clipboard.items.add(new window.File(['replacement'], 'new.jpg', { type: 'image/jpeg' }));
        window.document.dispatchEvent(new window.ClipboardEvent('paste', { clipboardData: clipboard }));
        await window.happyDOM.waitUntilComplete();

        expect(form.querySelector('.step').classList.contains('hidden')).toBe(false);
        expect(window.document.getElementById('review-step').classList.contains('hidden')).toBe(true);
    } finally {
        await window.happyDOM.close();
    }
});
