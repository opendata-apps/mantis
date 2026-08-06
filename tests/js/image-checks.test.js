import { describe, expect, test } from 'bun:test';
import { canvasIsBlank, extensionFor } from '../../app/static/js/image-checks.js';

// A row of `n` pixels, every channel set to `value`.
const row = (n, [r, g, b, a]) => {
    const data = new Uint8ClampedArray(n * 4);
    for (let i = 0; i < n; i += 1) data.set([r, g, b, a], i * 4);
    return data;
};

// A canvas whose rows are supplied by `rowFor(y)`, recording every read.
const fakeCtx = (rowFor) => {
    const calls = [];
    return {
        calls,
        getImageData: (x, y, w, h) => {
            calls.push([x, y, w, h]);
            return { data: rowFor(y, w) };
        },
    };
};

const uniform = (pixel) => fakeCtx((y, w) => row(w, pixel));

describe('canvasIsBlank', () => {
    test('an untouched canvas is transparent black', () => {
        expect(canvasIsBlank(uniform([0, 0, 0, 0]), 64, 64)).toBe(true);
    });

    test('the Cottbus signature (near-black but alpha 0) still counts as blank', () => {
        // Report 21953: 4000x3000, 256 px of (1,1,1,0), rest (0,0,0,0).
        expect(canvasIsBlank(uniform([1, 1, 1, 0]), 64, 64)).toBe(true);
    });

    test('an opaque photo is not blank', () => {
        expect(canvasIsBlank(uniform([12, 34, 56, 255]), 64, 64)).toBe(false);
    });

    test('one opaque pixel anywhere is enough to pass', () => {
        const ctx = fakeCtx((y, w) => {
            const data = row(w, [0, 0, 0, 0]);
            if (y === 0) data[4 * 9 + 3] = 255;
            return data;
        });
        expect(canvasIsBlank(ctx, 64, 64)).toBe(false);
    });

    test('a PNG with a transparent border is not blank', () => {
        const ctx = fakeCtx((y, w) =>
            row(w, y === 0 ? [0, 0, 0, 0] : [9, 9, 9, 255])
        );
        expect(canvasIsBlank(ctx, 64, 64)).toBe(false);
    });

    test('a getImageData failure is not treated as blank', () => {
        // Tainted or oversized canvas: "could not tell" must let the photo
        // through, because a false positive costs the sighting.
        const ctx = {
            getImageData: () => {
                throw new Error('SecurityError');
            },
        };
        expect(canvasIsBlank(ctx, 64, 64)).toBe(false);
    });

    test('reads full-width single-pixel rows within the canvas', () => {
        const ctx = uniform([0, 0, 0, 0]);
        canvasIsBlank(ctx, 100, 40);
        expect(ctx.calls.length).toBeGreaterThan(0);
        for (const [x, y, w, h] of ctx.calls) {
            expect([x, w, h]).toEqual([0, 100, 1]);
            expect(y).toBeGreaterThanOrEqual(0);
            expect(y).toBeLessThan(40);
        }
    });

    test('never samples more rows than the canvas has', () => {
        const ctx = uniform([0, 0, 0, 0]);
        canvasIsBlank(ctx, 10, 3);
        expect(ctx.calls.length).toBe(3);
    });

    test('samples a bounded number of rows on a tall canvas', () => {
        // The whole point of sampling: a 2048-row readback would allocate 16MB.
        const ctx = uniform([0, 0, 0, 0]);
        canvasIsBlank(ctx, 2048, 2048);
        expect(ctx.calls.length).toBeLessThanOrEqual(16);
    });
});

describe('extensionFor', () => {
    // Must stay in step with FileAllowed in app/forms.py, which validates the
    // extension of whatever the fallback forwards.
    test.each([
        ['image/jpeg', '.jpg'],
        ['image/png', '.png'],
        ['image/webp', '.webp'],
        ['image/heic', '.heic'],
        ['image/heif', '.heif'],
    ])('%s -> %s', (type, expected) => {
        expect(extensionFor(type)).toBe(expected);
    });

    test('an unknown type falls back to the converted extension', () => {
        // Android pickers can hand over a File with an empty type.
        expect(extensionFor('')).toBe('.webp');
        expect(extensionFor('image/gif')).toBe('.webp');
    });
});
