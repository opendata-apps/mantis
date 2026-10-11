import { expect, test } from 'bun:test';
import { Window } from 'happy-dom';

const bundle = await Bun.build({
    entrypoints: [new URL('../../app/static/js/gallery.js', import.meta.url).pathname],
    target: 'browser', format: 'iife', write: false,
});
if (!bundle.success) throw new AggregateError(bundle.logs, 'Gallery bundle failed');
const source = await bundle.outputs[0].text();

// An album of /a.webp, /b.webp, /c.webp, opened on /a.webp.
async function withOpenLightbox(run) {
    const window = new Window({ settings: { enableJavaScriptEvaluation: true, suppressInsecureJavaScriptEnvironmentWarning: true } });
    try {
        const document = window.document;
        document.body.innerHTML = `
            <a href="/a.webp" data-lightbox="album">A</a>
            <a href="/b.webp" data-lightbox="album">B</a>
            <a href="/c.webp" data-lightbox="album">C</a>
            <dialog id="lightbox">
                <img class="lightbox-img" alt="">
                <div class="lightbox-caption"></div><span class="lightbox-counter"></span>
                <a class="lightbox-newtab" hidden></a>
                <button class="lightbox-close"></button>
                <button class="lightbox-prev" hidden></button><button class="lightbox-next" hidden></button>
            </dialog>`;
        window.eval(source);
        document.dispatchEvent(new window.Event('DOMContentLoaded'));
        document.querySelector('a[data-lightbox]').click();
        const dialog = document.getElementById('lightbox');
        // A finger is [id, screenX]. touches lists the fingers still down;
        // changedTouches the ones that just landed or lifted.
        const finger = ([identifier, screenX]) => new window.Touch({ identifier, target: dialog, screenX });
        const touch = (type, down, changed) => dialog.dispatchEvent(new window.TouchEvent(type, {
            touches: down.map(finger), changedTouches: changed.map(finger),
        }));
        await run({ touch, photo: () => dialog.querySelector('.lightbox-img').getAttribute('src') });
    } finally {
        await window.happyDOM.close();
    }
}

test('a pinch-zoom on the photo keeps the photo', async () => {
    await withOpenLightbox(({ touch, photo }) => {
        // Lopsided pinch: finger 1 sweeps 180 → 60, finger 2 barely moves
        // 220 → 230. In a symmetric pinch the two lifts read as opposite
        // swipes and cancel out, which would hide the bug.
        touch('touchstart', [[1, 180]], [[1, 180]]);
        touch('touchstart', [[1, 180], [2, 220]], [[2, 220]]);
        touch('touchend', [[2, 230]], [[1, 60]]);
        touch('touchend', [], [[2, 230]]);

        expect(photo()).toBe('/a.webp');
    });
});

test('a one-finger swipe after a pinch still pages', async () => {
    await withOpenLightbox(({ touch, photo }) => {
        touch('touchstart', [[1, 180]], [[1, 180]]);
        touch('touchstart', [[1, 180], [2, 220]], [[2, 220]]);
        touch('touchend', [[2, 230]], [[1, 60]]);
        touch('touchend', [], [[2, 230]]);
        // Swipe left, 150px.
        touch('touchstart', [[3, 300]], [[3, 300]]);
        touch('touchend', [], [[3, 150]]);

        expect(photo()).toBe('/b.webp');
    });
});
