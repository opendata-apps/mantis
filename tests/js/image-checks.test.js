import { describe, expect, test } from 'bun:test';
import { canvasIsBlank, extensionFor } from '../../app/static/js/image-checks.js';

// Canvas readback with arbitrary rectangular regions and a measurable byte budget.
const fakeCtx = (pixelAt) => {
    const reads = [];
    return {
        reads,
        getImageData: (x, y, w, h) => {
            const data = new Uint8ClampedArray(w * h * 4);
            for (let row = 0; row < h; row += 1) {
                for (let col = 0; col < w; col += 1) {
                    data.set(pixelAt(x + col, y + row), (row * w + col) * 4);
                }
            }
            reads.push({ x, y, w, h, bytes: data.byteLength });
            return { data };
        },
    };
};
const uniform = (pixel) => fakeCtx(() => pixel);

describe('canvasIsBlank', () => {
    test('an untouched canvas is transparent black', () => {
        expect(canvasIsBlank(uniform([0, 0, 0, 0]), 64, 64)).toBe(true);
    });

    test('the Cottbus signature (near-black but alpha 0) still counts as blank', () => {
        expect(canvasIsBlank(uniform([1, 1, 1, 0]), 64, 64)).toBe(true);
    });

    test('an opaque photo is not blank', () => {
        expect(canvasIsBlank(uniform([12, 34, 56, 255]), 64, 64)).toBe(false);
    });

    test('an opaque pixel in the sampled top row is not blank', () => {
        const ctx = fakeCtx((x, y) => [0, 0, 0, x === 9 && y === 0 ? 255 : 0]);
        expect(canvasIsBlank(ctx, 64, 64)).toBe(false);
    });

    test('a PNG with a transparent border is not blank', () => {
        const ctx = fakeCtx((x, y) =>
            x === 0 || y === 0 || x === 63 || y === 63 ? [0, 0, 0, 0] : [9, 9, 9, 255]
        );
        expect(canvasIsBlank(ctx, 64, 64)).toBe(false);
    });

    test('a getImageData failure is not treated as blank', () => {
        const ctx = { getImageData: () => { throw new Error('SecurityError'); } };
        expect(canvasIsBlank(ctx, 64, 64)).toBe(false);
    });

    test.each([[100, 40], [10, 3]])('readback stays inside a %sx%s canvas', (width, height) => {
        const ctx = uniform([0, 0, 0, 0]);
        expect(canvasIsBlank(ctx, width, height)).toBe(true);
        expect(ctx.reads.length).toBeGreaterThan(0);
        for (const { x, y, w, h } of ctx.reads) {
            expect(x).toBeGreaterThanOrEqual(0);
            expect(y).toBeGreaterThanOrEqual(0);
            expect(w).toBeGreaterThan(0);
            expect(h).toBeGreaterThan(0);
            expect(x + w).toBeLessThanOrEqual(width);
            expect(y + h).toBeLessThanOrEqual(height);
        }
    });

    test('a large canvas uses at most 128 KiB of readback', () => {
        const ctx = uniform([0, 0, 0, 0]);
        expect(canvasIsBlank(ctx, 2048, 2048)).toBe(true);
        expect(ctx.reads.reduce((bytes, read) => bytes + read.bytes, 0)).toBeLessThanOrEqual(128 * 1024);
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
