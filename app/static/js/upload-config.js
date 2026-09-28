// Reads the photo rules the server renders into #upload-config. The single
// source is app/tools/image_upload.py; nothing here restates a format or a size.

let cached = null;

export function uploadConfig() {
    if (cached) return cached;
    const block = document.getElementById('upload-config');
    if (!block) {
        // Fail loudly rather than guess the rules.
        throw new Error('#upload-config is missing — render_photo_upload not on this page?');
    }
    cached = JSON.parse(block.textContent);
    return cached;
}
