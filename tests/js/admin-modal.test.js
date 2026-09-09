import { expect, test } from 'bun:test';
import { Window } from 'happy-dom';

const bundle = await Bun.build({
    entrypoints: [new URL('../../app/static/js/admin-modal.js', import.meta.url).pathname],
    target: 'browser', format: 'iife', write: false,
});
if (!bundle.success) throw new AggregateError(bundle.logs, 'Admin bundle failed');
const source = await bundle.outputs[0].text();

test('clearing filters submits the default selection and preserves the search', async () => {
    const window = new Window({ settings: { enableJavaScriptEvaluation: true, suppressInsecureJavaScriptEnvironmentWarning: true } });
    try {
        const document = window.document;
        document.body.dataset.coordRange = JSON.stringify({ latitude: [24.6, 60], longitude: [-20, 44.83] });
        document.body.innerHTML = `
            <form>
                <select id="statusInput" name="statusInput">
                    <option value="offen">Offen</option><option value="all" selected>Alle</option>
                </select>
                <select id="typeInput" name="typeInput">
                    <option value="all">Alle</option><option value="maennlich" selected>Männlich</option>
                </select>
                <input id="dateFrom" name="dateFrom" value="01.01.2025">
                <input id="dateTo" name="dateTo" value="31.12.2025">
                <input id="dateType" name="dateType" value="meld" type="hidden">
                <input name="q" value="existing search" type="hidden">
                <input name="sort_order" value="id_desc" type="hidden">
                <input name="search_type" value="full_text" type="hidden">
                <button id="clearFilters" type="button">Filter löschen</button>
            </form>`;
        const submissions = [];
        const form = document.querySelector('form');
        form.submit = () => submissions.push(Object.fromEntries(new window.FormData(form)));
        window.eval(source);
        document.dispatchEvent(new window.Event('DOMContentLoaded'));
        document.getElementById('clearFilters').click();

        expect(submissions).toEqual([{
            statusInput: 'offen', typeInput: 'all', dateFrom: '', dateTo: '',
            dateType: 'fund', q: 'existing search', sort_order: 'id_desc', search_type: 'full_text',
        }]);
    } finally {
        await window.happyDOM.close();
    }
});


test('coordinate edits reject numeric prefixes and accept decimal commas', async () => {
    const window = new Window({ settings: { enableJavaScriptEvaluation: true, suppressInsecureJavaScriptEnvironmentWarning: true } });
    try {
        const document = window.document;
        document.body.dataset.coordRange = JSON.stringify({ latitude: [24.6, 60], longitude: [-20, 44.83] });
        document.body.innerHTML = `<form id="coord-update-form">
            <input name="latitude" value="52,52km">
            <input name="longitude" value="13,405">
        </form>`;
        const saved = [];
        const form = document.getElementById('coord-update-form');
        form.addEventListener('coord-valid', () => saved.push(Object.fromEntries(new window.FormData(form))));
        window.eval(source);
        const latitude = form.querySelector('[name=latitude]');
        window.validateAndUpdateCoordinate(latitude, 'latitude');
        expect(saved).toEqual([]);
        expect(latitude.classList.contains('border-red-500')).toBe(true);
        latitude.value = '52,52';
        window.validateAndUpdateCoordinate(latitude, 'latitude');
        expect(saved).toEqual([{latitude: '52,52', longitude: '13,405'}]);
        expect(latitude.classList.contains('border-red-500')).toBe(false);
    } finally {
        await window.happyDOM.close();
    }
});
