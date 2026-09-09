// Guards for the client-side photo pipeline, kept pure so they can be tested
// without a DOM. See tests/js/image-checks.test.js.

// Sample rows rather than the whole canvas: a 2048x2048 getImageData allocates
// 16MB in one go on exactly the memory-starved phones this guard exists for.
const SAMPLE_ROWS = 16;

const sampleRows = (ctx, width, height) => {
    const rows = [];
    const step = Math.max(1, Math.floor(height / SAMPLE_ROWS));
    try {
        for (let y = 0; y < height && rows.length < SAMPLE_ROWS; y += step) {
            rows.push(ctx.getImageData(0, y, width, 1).data);
        }
    } catch {
        // Tainted or oversized canvas: report "unknown" so the photo proceeds.
        return [];
    }
    return rows;
};

// A canvas that never received pixels keeps its initial value — transparent
// black — and `drawImage` can silently no-op in an Android WebView without
// throwing, so a fully zero alpha channel is what "the draw did nothing" looks
// like. Photos are opaque, so a single non-zero alpha clears the check.
// No samples means "could not tell" and must NOT read as blank.
export const canvasIsBlank = (ctx, width, height) => {
    const rows = sampleRows(ctx, width, height);
    return (
        rows.length > 0 &&
        rows.every((data) => {
            for (let i = 3; i < data.length; i += 4) {
                if (data[i] !== 0) return false;
            }
            return true;
        })
    );
};

// FileAllowed on the server validates the extension, so an original forwarded
// by the fallback would be rejected on a technicality under the wrong one.
// Every type imageType() admits is decodable server-side (Pillow, plus
// pillow-heif for HEIC), so there is no format the fallback has to refuse.
const EXT_BY_TYPE = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
    'image/heic': '.heic',
    'image/heif': '.heif',
};

export const extensionFor = (type) => EXT_BY_TYPE[type] || '.webp';
