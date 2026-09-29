/**
 * HTMX Report Form - Minimal JS for photo/map handling
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { geocoder } from 'leaflet-control-geocoder';
import 'leaflet-control-geocoder/dist/Control.Geocoder.css';
import { locate } from 'leaflet.locatecontrol';
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css';
import ExifReader from 'exifreader';
import htmx from 'htmx.org';
import { canvasIsBlank, extensionFor } from './image-checks.js';
import { coordinatesInRange, parseCoordinateInput } from './coordinate-input.js';
import { uploadConfig } from './upload-config.js';

// Configure HTMX to include CSRF token in all requests
// This is the recommended approach from Flask-WTF documentation for AJAX requests
document.body.addEventListener('htmx:configRequest', (event) => {
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken;
    }
});

// Leaflet guesses this path from its stylesheet, where Vite inlines the image.
L.Icon.Default.mergeOptions({ imagePath: '/static/images/map/' });

// Error containers whose id does not match the input the user actually types in.
// The hidden latitude/longitude fields share one container next to the map.
const ERROR_INPUT = { coordinates: 'manual-latitude' };

const CONNECTION_ERROR = 'Verbindung zum Server fehlgeschlagen. '
    + 'Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.';

const ReportForm = {
    initialized: false,
    submitting: false,
    dirty: false,
    stepTitles: ['Foto & Details', 'Ort & Datum', 'Kontaktdaten', 'Überprüfen'],
    map: null,
    marker: null,
    webpData: null,
    geocodeController: null,
    coordinateRanges: null,
    locUpdates: 0,
    bestAccuracy: Infinity,
    locTimeout: null,
    MIN_ZOOM: 17,

    init() {
        const form = document.getElementById('reportForm');
        if (!form) return;

        this.reviewUrl = form.dataset.reviewUrl;
        this.agsUrl = form.dataset.agsUrl;

        this.setupNav();
        this.setupPhoto();
        this.initMap();
        this.setupHtmx(form);
        this.showStep(0);

        // Dirty-form guard: warn before closing tab with unsaved data
        window.addEventListener('beforeunload', (e) => {
            if (this.dirty && !this.submitting) {
                e.preventDefault();
                e.returnValue = true; // browsers without the preventDefault() trigger
            }
        });
        form.addEventListener('input', () => { this.dirty = true; });

        const description = document.getElementById('description');
        const remaining = document.getElementById('char-count');
        description?.addEventListener('input', () => {
            remaining.textContent = description.maxLength - description.value.length;
        });
    },

    setupNav() {
        document.addEventListener('click', (e) => {
            const prev = e.target.closest('[data-prev-step]');
            if (prev) return this.showStep(parseInt(prev.dataset.prevStep, 10) - 2);

            const edit = e.target.closest('.edit-btn');
            if (edit) this.showStep(parseInt(edit.dataset.step, 10) - 1);
        });
    },

    showStep(i) {
        const steps = document.querySelectorAll('.step');
        if (i < 0 || i >= steps.length) return;

        steps.forEach((s, idx) => {
            s.classList.toggle('hidden', idx !== i);
        });

        document.title = `${this.stepTitles[i]} – Sichtung melden`;

        // Move focus to the new step's heading (skip on initial load to avoid jarring scroll)
        if (this.initialized) {
            const heading = steps[i].querySelector('h3');
            if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus(); }
        }
        this.initialized = true;

        if (i === 1 && this.map) {
            // The map was measured while its step was hidden.
            this.map.invalidateSize();
            this.autoLocateIfNeeded();
        }
        if (i === 3) this.loadReview();
    },

    setupHtmx(form) {
        document.body.addEventListener('htmx:beforeRequest', (e) => {
            this.clearError('general');
            const btn = e.target.closest('[data-step]');
            if (!btn) return;
            const step = parseInt(btn.dataset.step, 10);

            if (step === 1 && !this.webpData) {
                e.preventDefault();
                this.showError('photo', 'Bitte laden Sie ein Foto hoch.');
            } else if (step === 2 && (!document.getElementById('latitude')?.value || !document.getElementById('longitude')?.value)) {
                e.preventDefault();
                this.showError('coordinates', 'Bitte wählen Sie einen Standort auf der Karte.');
            }
        });

        // htmx swaps no 4xx/5xx response, so without these a failed step
        // check leaves "Weiter" doing nothing at all.
        document.body.addEventListener('htmx:responseError', (e) => {
            const { xhr } = e.detail;
            let json = null;
            if (xhr.getResponseHeader('Content-Type')?.includes('application/json')) {
                try { json = JSON.parse(xhr.responseText); } catch { /* generic message */ }
            }
            this.showError('general', json?.error
                || 'Ihre Angaben konnten nicht geprüft werden. Bitte versuchen Sie es erneut.');
        });
        document.body.addEventListener('htmx:sendError', () => this.showError('general', CONNECTION_ERROR));

        document.body.addEventListener('stepValid', (e) => {
            this.clearErrors();
            this.showStep(e.detail.nextStep - 1);
        });

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submit(form);
        });

        // Inject photo preview after review content is swapped in (avoids ~4MB base64 round-trip)
        document.body.addEventListener('htmx:afterSwap', (e) => {
            if (e.detail.target.id === 'review-content-container') {
                const img = document.getElementById('review-photo');
                if (img && this.webpData?.previewSrc) {
                    img.src = this.webpData.previewSrc;
                }
            }
            // After validation swap, wire aria attributes on invalid fields and focus the first one
            if (e.detail.target.id === 'validation-errors-container') {
                this.syncAriaErrors();
            }
        });
    },

    syncAriaErrors() {
        let firstInvalid = null;

        document.querySelectorAll('.field-error-message').forEach(el => {
            const field = el.id.replace('error-', '');
            const input = document.getElementById(ERROR_INPUT[field] || field);
            if (!input) return;

            // A hint (e.g. the photo fallback notice) occupies the same slot but is not a rejection.
            const hasError = !el.classList.contains('is-hint') && el.textContent.trim().length > 0;
            if (hasError) {
                input.setAttribute('aria-invalid', 'true');
                input.setAttribute('aria-describedby', el.id);
                if (!firstInvalid) firstInvalid = input;
            } else {
                input.removeAttribute('aria-invalid');
                input.removeAttribute('aria-describedby');
            }
        });

        if (firstInvalid) firstInvalid.focus();
    },

    loadReview() {
        const form = document.getElementById('reportForm');
        const data = new FormData(form);
        // The review shows the local preview (htmx:afterSwap), so the photo stays here.
        data.delete('photo');
        htmx.ajax('POST', this.reviewUrl, {
            target: '#review-content-container',
            swap: 'innerHTML',
            values: Object.fromEntries(data)
        });
    },

    async submit(form) {
        if (this.submitting) return;
        this.submitting = true;

        if (!this.webpData?.blob) {
            this.submitting = false;
            this.showError('photo', 'Kein Foto vorhanden.');
            return this.showStep(0);
        }

        this.showLoading(true);
        try {
            const data = new FormData(form);
            data.delete('photo');
            const ext = extensionFor(this.webpData.blob.type, uploadConfig().extensionByMime);
            const name = (this.webpData.fileName || 'photo').replace(/\.[^.]+$/, ext);
            data.append('photo', new File([this.webpData.blob], name, { type: this.webpData.blob.type }));

            const res = await fetch(form.action, {
                method: 'POST',
                body: data,
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value,
                    'Accept': 'application/json'
                }
            });

            const contentType = res.headers.get('content-type') || '';
            const json = contentType.includes('application/json')
                ? await res.json().catch(() => null)
                : null;

            if (!res.ok || !json?.success || !json?.redirect_url) {
                this.submitting = false;
                this.showLoading(false);
                // A field-level rejection on the last step is otherwise a dead end:
                // the review page cannot show which answer the server refused.
                if (json?.errors && Object.keys(json.errors).length) {
                    return this.showServerErrors(json.errors);
                }
                return this.showError('general', json?.error
                    || 'Die Meldung konnte nicht gespeichert werden. Bitte versuchen Sie es erneut.');
            }

            this.dirty = false;
            window.location.href = json.redirect_url;
        } catch {
            this.submitting = false;
            this.showLoading(false);
            this.showError('general', CONNECTION_ERROR);
        }
    },

    // The DOM already records which step owns a field, so the field -> step
    // mapping never has to be restated in JS.
    stepOfField(name) {
        const el = document.getElementById(name) || document.getElementById(`error-${name}`);
        const step = el?.closest('.step');
        return step ? [...document.querySelectorAll('.step')].indexOf(step) : -1;
    },

    showServerErrors(errors) {
        this.clearErrors();

        let target = Infinity;
        const unplaced = [];
        for (const [slot, messages] of Object.entries(errors)) {
            const msg = Array.isArray(messages) ? messages[0] : String(messages);
            // Not every field has an error container (finder names, feedback).
            // Those messages still have to reach the user somewhere.
            if (!document.getElementById(`error-${slot}`)) {
                unplaced.push(msg);
                continue;
            }
            this.showError(slot, msg, false);
            const step = this.stepOfField(slot);
            if (step >= 0 && step < target) target = step;
        }

        if (target === Infinity) {
            // Nothing could be pinned to a step — keep the user on the review
            // page, where the general error box is visible.
            return this.showError('general',
                unplaced.join(' ') || 'Bitte prüfen Sie Ihre Angaben.');
        }
        this.showStep(target);
        document.querySelectorAll('.step')[target]
            ?.querySelector('[aria-invalid="true"]')?.focus();
    },

    setupPhoto() {
        const input = document.getElementById('photo');
        const dropzone = document.getElementById('photo-upload-area');
        if (!input || !dropzone) return;

        input.addEventListener('change', (e) => this.handlePhoto(e.target.files?.[0]));
        // The <label> already activates the input. Letting its click bubble to
        // the dropzone opens the Android picker a second time, and the second
        // intent cancels the first selection — the form then looks untouched.
        dropzone.addEventListener('click', (e) => {
            if (!e.target.closest('label')) input.click();
        });
        dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
        dropzone.addEventListener('dragleave', (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); });
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                input.files = e.dataTransfer.files;
                this.handlePhoto(e.dataTransfer.files[0]);
            }
        });
        // On a desktop the clipboard is often the only route a phone photo takes
        // onto the machine. Read `items`: Safari leaves `clipboardData.files`
        // empty while still carrying the image.
        document.addEventListener('paste', (e) => {
            // Office and LibreOffice put a rendered PNG beside copied text; the
            // text wins. Image copies and screenshots carry no text/plain.
            if (e.clipboardData?.getData('text/plain').trim()) return;
            const item = [...(e.clipboardData?.items ?? [])].find(
                (i) => i.kind === 'file' && i.type.startsWith('image/'));
            const blob = item?.getAsFile();
            if (!blob) return;
            e.preventDefault();
            // Browsers re-encode clipboard images to PNG and hand them over as
            // "image.png", so the name carries nothing and EXIF is already gone.
            const ext = blob.type.split('/')[1].replace('jpeg', 'jpg');
            const pasted = new File([blob], `einfuegen-${Date.now()}.${ext}`, { type: blob.type });
            const transfer = new DataTransfer();
            transfer.items.add(pasted);
            input.files = transfer.files;
            this.handlePhoto(pasted);
        });
        document.getElementById('remove-photo')?.addEventListener('click', () => this.removePhoto());
    },

    async handlePhoto(file) {
        if (!file) return;
        const type = this.imageType(file);
        if (!type) return this.showError('photo', 'Ungültiges Bildformat.');
        const { maxBytes, maxMb } = uploadConfig();
        if (file.size > maxBytes) return this.showError('photo',
            `Das Foto ist größer als ${maxMb} MB. Bitte wählen Sie ein kleineres Foto `
            + 'oder stellen Sie die Kamera auf eine geringere Auflösung (z. B. 12 MP).');

        this.clearError('photo');
        this.setDropzoneLoading(true, 'Bild wird verarbeitet...');

        // Start the read here, still inside the change event's own task: Android
        // hands gallery items over as proxy content:// URIs that can turn
        // unreadable moments later.
        const read = file.arrayBuffer();
        let exif = {};

        try {
            const bytes = await this.stage('read', read);
            exif = this.extractExif(bytes);
            this.setPhoto(await this.toWebp(bytes, type, file.size), file.name);
        } catch (err) {
            const probe = err.stage === 'read' ? await this.probeRead(file) : '';
            const escalation = await this.reportPhotoFailure(file, err, probe);

            // The server decodes every accepted format, so a failed conversion
            // forwards the original. A failed read does not: submit would fail too.
            if (err.stage === 'read') {
                // Reset before showing: removePhoto() clears the photo error, so
                // the other order erases the message the user needs to see.
                this.removePhoto();
                this.showError('photo',
                    'Ihr Gerät hat dieses Foto nicht an den Browser übergeben. Das liegt nicht '
                    + 'am Foto, sondern an einem Fehler, der auf manchen Android-Handys '
                    + 'auftritt. Bitte wählen Sie ein anderes Foto — klappt es '
                    + 'weiterhin nicht, erscheint hier ein Weg, es uns per E-Mail zu schicken.');
                this.showEscalation(escalation);
                return;
            }

            this.setPhoto(file, file.name);
            this.showHint('photo',
                'Das Foto konnte im Browser nicht verkleinert werden und wird unverändert '
                + 'hochgeladen — das kann etwas länger dauern.');
        } finally {
            this.setDropzoneLoading(false);
        }

        this.applyExif(exif);
    },

    // The converted blob and the untouched original are shown and submitted the same way.
    setPhoto(blob, fileName) {
        this.hideEscalation();
        this.releasePreview();
        this.webpData = { previewSrc: URL.createObjectURL(blob), blob, fileName };
        this.dirty = true;

        document.getElementById('photo-upload-area')?.classList.add('hidden');
        const preview = document.getElementById('photoPreview');
        const img = document.getElementById('preview-img');
        if (preview && img) {
            preview.classList.remove('hidden');
            img.src = this.webpData.previewSrc;
        }
    },

    // A blob: URL pins the photo in memory until it is revoked.
    releasePreview() {
        if (this.webpData) URL.revokeObjectURL(this.webpData.previewSrc);
    },

    // Android pickers sometimes deliver a File with an empty `type`, so the
    // extension has to be able to stand in for it — and vice versa.
    imageType(file) {
        const types = uploadConfig().types;
        const ext = (file.name || '').toLowerCase().split('.').pop();
        const type = (file.type || '').toLowerCase();
        if (Object.values(types).includes(type)) return type;
        return types[ext] || null;
    },

    // One catch covers the whole pipeline, so each step has to name itself —
    // the label is what tells the user and the failure report which one broke.
    async stage(name, work) {
        try {
            return await work;
        } catch (cause) {
            throw this.photoError(name, cause);
        }
    },

    photoError(stage, cause) {
        // Both halves matter: the name carries the browser's verdict
        // (NotReadableError, SecurityError), the message the detail.
        const detail = cause ? `${cause.name || 'Error'} ${cause.message || ''}`.trim() : 'no detail';
        const err = new Error(`${stage}: ${detail}`);
        err.stage = stage;
        return err;
    },

    // Chrome reports every Android device as "Android 10; K", so only client hints
    // name the model. Chromium-only: elsewhere this is {} and the server reads the UA.
    async deviceHints() {
        try {
            const hints = await navigator.userAgentData?.getHighEntropyValues?.(
                ['model', 'platformVersion']);
            return {
                model: hints?.model || '',
                osVersion: hints?.platformVersion || '',
                platform: hints?.platform || '',
            };
        } catch {
            return {};
        }
    },

    // Tells the Android photo picker (168243243.jpg) from DocumentsUI, which passes
    // the gallery name. Only the class travels: a file name can identify a person.
    nameShape(name) {
        const base = (name || '').replace(/\.[^.]*$/, '');
        if (!base) return 'empty';
        return /^\d+$/.test(base) ? 'numeric' : 'named';
    },

    // Inside Chrome a 'read' failure is one of two faults: the provider refuses
    // to reopen the file, or it delivers a byte count other than the size it
    // reported. A small slice needs only the open; the stream counts what arrives.
    // Bounded, because the failure message waits for it.
    async probeRead(file) {
        const probe = (async () => {
            const head = await file.slice(0, 65536).arrayBuffer().then(() => 'ok', (e) => e.name);
            let bytes = 0;
            try {
                const reader = file.stream().getReader();
                for (;;) {
                    // oxlint-disable-next-line no-await-in-loop -- a stream reads in order
                    const { done, value } = await reader.read();
                    if (done) return `head=${head} stream=${bytes}/done`;
                    bytes += value.byteLength;
                }
            } catch (e) {
                return `head=${head} stream=${bytes}/${e.name}`;
            }
        })();
        const timeout = new Promise((resolve) => setTimeout(() => resolve('timeout'), 5000));
        return Promise.race([probe, timeout]);
    },

    // Reports the failing step and the file class, never the image. Resolves to the
    // server's escalation payload once it has counted enough failures, else null.
    async reportPhotoFailure(file, err, probe) {
        const url = document.getElementById('reportForm')?.dataset.photoErrorUrl;
        if (!url) return null;
        const hints = await this.deviceHints();
        try {
            const res = await fetch(url, {
                method: 'POST',
                keepalive: true,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value
                },
                body: JSON.stringify({
                    stage: err?.stage || 'unbekannt',
                    error: String(err?.message || err).slice(0, 200),
                    size: file?.size ?? null,
                    // Two re-picks of the same photo reporting two different values
                    // is Chromium's proxy-URI bug; 0 means the picker never
                    // resolved the item at all.
                    mtime: file?.lastModified ?? null,
                    type: file?.type || '',
                    ext: (file?.name || '').toLowerCase().split('.').pop().slice(0, 10),
                    name: this.nameShape(file?.name),
                    probe,
                    model: hints.model || '',
                    osVersion: hints.osVersion || '',
                    platform: hints.platform || ''
                })
            });
            return res.status === 200 ? await res.json() : null;
        } catch {
            return null; // diagnostics must never turn into a second failure
        }
    },

    // After repeated failures, offer the one channel that still works: the mail
    // app reaches the gallery by a different route than the upload does, so it
    // can attach a photo the browser was unable to read.
    showEscalation(payload) {
        const box = document.getElementById('photo-escalation');
        const link = document.getElementById('photo-escalation-link');
        if (!box || !link || !payload?.mailto) return;
        link.href = payload.mailto;
        box.classList.remove('hidden');
    },

    hideEscalation() {
        document.getElementById('photo-escalation')?.classList.add('hidden');
    },

    // Autofill only: a photo whose metadata cannot be parsed still uploads.
    extractExif(bytes) {
        let tags;
        try {
            tags = ExifReader.load(bytes, { expanded: true });
        } catch {
            return {};
        }
        const dateTime = tags.exif?.DateTimeOriginal?.description || tags.exif?.DateTime?.description;
        const gps = (typeof tags.gps?.Latitude === 'number' && typeof tags.gps?.Longitude === 'number')
            ? { lat: tags.gps.Latitude, lng: tags.gps.Longitude }
            : null;
        return { dateTime, gps };
    },

    // An object URL, not a data URL, so no base64 copy of the photo sits in memory.
    decode(blob) {
        const url = URL.createObjectURL(blob);
        return new Promise((res, rej) => {
            const el = new Image();
            el.addEventListener('load', () => res(el));
            el.addEventListener('error', () => rej(new Error('image decode failed')));
            el.src = url;
        }).finally(() => URL.revokeObjectURL(url));
    },

    async toWebp(bytes, type, size) {
        const blob = new Blob([bytes], { type });

        // Safari 17+ decodes HEIC natively, so try the browser first and only
        // pull in the 1.3MB wasm converter when it can't — which is also the
        // path that keeps working if the unmaintained heic2any ever breaks.
        let failure = null;
        let img = await this.decode(blob).catch((cause) => { failure = cause; return null; });
        if (!img && (type.includes('heic') || type.includes('heif'))) {
            const { default: heic2any } = await import('heic2any');
            // libheif never settles when its wasm cannot run or stalls, which
            // strands the user on the spinner with nothing to act on.
            const jpeg = await this.stage('heic', Promise.race([
                heic2any({ blob, toType: 'image/jpeg', quality: 0.85 }),
                new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 25000))
            ]));
            img = await this.stage('decode', this.decode(jpeg));
        }
        if (!img) throw this.photoError('decode', failure);

        // The server archives at most 2048 px and keeps a client WebP as is.
        const maxDim = 2048;
        let w = img.naturalWidth, h = img.naturalHeight;
        if (w > maxDim || h > maxDim) {
            const ratio = w / h;
            if (w > h) { w = maxDim; h = Math.round(maxDim / ratio); }
            else { h = maxDim; w = Math.round(maxDim * ratio); }
        }

        let canvas, ctx;
        try {
            canvas = document.createElement('canvas');
            canvas.width = w; canvas.height = h;
            ctx = canvas.getContext('2d');
            // A 12MP phone photo is a ~2.3x reduction in one step; without this
            // the default bilinear filter aliases fine detail (wing venation).
            ctx.imageSmoothingQuality = 'high';
            ctx.drawImage(img, 0, 0, w, h);
        } catch (cause) {
            throw this.photoError('canvas', cause);
        }

        // drawImage can no-op without throwing in an Android WebView, leaving a
        // transparent frame. A verdict, not a native fault, so it keeps its own label.
        if (canvasIsBlank(ctx, w, h)) throw this.photoError('blank-canvas');

        const sizeMB = size / 1048576;
        const pixels = w * h;
        let q = sizeMB > 10 ? 0.6 : sizeMB > 5 ? 0.7 : 0.8;
        if (pixels > 8e6) q = Math.min(q, 0.6);
        else if (pixels > 4e6) q = Math.min(q, 0.7);

        const encode = (mime) => new Promise((r) => canvas.toBlob(r, mime, q));
        // WebKit cannot encode WebP, and toBlob falls back to PNG for an unsupported
        // type (HTML spec) or yields null. JPEG is encoded everywhere.
        let mime = 'image/webp';
        let out = await encode(mime);
        if (!out || out.type !== mime) {
            mime = 'image/jpeg';
            out = await encode(mime);
        }
        if (!out) throw this.photoError('encode');

        // WebKit only frees a canvas once it is resized away (bug 195325), and on
        // a phone this is the largest allocation the form makes.
        canvas.width = canvas.height = 0;
        return out;
    },

    removePhoto() {
        const input = document.getElementById('photo');
        if (input) input.value = '';
        document.getElementById('photoPreview')?.classList.add('hidden');
        document.getElementById('exif-data')?.classList.add('hidden');
        document.getElementById('photo-upload-area')?.classList.remove('hidden');
        const img = document.getElementById('preview-img');
        if (img) img.src = '';
        this.releasePreview();
        this.webpData = null;
        this.clearError('photo');
    },

    applyExif({ dateTime, gps }) {
        let hasData = false;
        const dateInput = document.getElementById('sighting_date');
        const exifDate = document.getElementById('exif-date');

        if (dateTime && dateInput) {
            const [datePart] = dateTime.split(' ');
            const [y, m, d] = datePart.split(':');
            const formatted = `${y}-${m}-${d}`;
            const date = new Date(formatted);
            if (!isNaN(date) && date <= new Date()) {
                dateInput.value = formatted;
                if (exifDate) exifDate.textContent = date.toLocaleDateString('de-DE');
                hasData = true;
            }
        }

        // A camera without a fix writes a zeroed tag, and a wrong hemisphere ref
        // flips a sign; such a position leaves the map to the reporter.
        if (gps && this.map && coordinatesInRange(gps.lat, gps.lng, this.coordinateRanges)) {
            const { lat, lng } = gps;
            const exifLocation = document.getElementById('exif-location');
            if (exifLocation) exifLocation.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;

            this.map.setView([lat, lng], this.MIN_ZOOM);
            this.setMarker(lat, lng, true);
            hasData = true;
        }

        if (hasData) document.getElementById('exif-data')?.classList.remove('hidden');
    },

    initMap() {
        const container = document.getElementById('map');
        if (!container) return;

        this.coordinateRanges = JSON.parse(document.body.dataset.coordRange);

        this.map = L.map(container, { zoomControl: true, attributionControl: false })
            .setView([51.1657, 10.4515], 6);
        L.control.attribution({ prefix: false }).addTo(this.map);

        const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18, minZoom: 3, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        });
        const esriImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 18, minZoom: 3, attribution: 'Tiles &copy; Esri',
        });
        const esriLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 18, minZoom: 3, attribution: 'Tiles &copy; Esri',
        });

        this.map.addLayer(osmLayer);
        L.control.layers({ 'Karte': osmLayer, 'Satellit': L.layerGroup([esriImagery, esriLabels]) }).addTo(this.map);

        geocoder({ defaultMarkGeocode: false, placeholder: 'Adresse suchen...' })
            .on('markgeocode', (e) => {
                // Auto-place marker when user searches for an address
                this.map.setView(e.geocode.center, this.MIN_ZOOM);
                this.setMarker(e.geocode.center.lat, e.geocode.center.lng);
            })
            .addTo(this.map);

        this.locateCtrl = locate({
            watch: true, setView: false, keepCurrentZoomLevel: true,
            drawCircle: false, drawMarker: false, showPopup: false,
            enableHighAccuracy: true, timeout: 15000, maximumAge: 30000,
            strings: { title: 'Standort' }
        }).addTo(this.map);
        this.map.on('locationfound', (e) => this.handleLocationFound(e));
        this.map.on('locationerror', () => this.stopLocationUpdates());

        this.map.on('click', (e) => {
            if (this.map.getZoom() < this.MIN_ZOOM) {
                this.showError('coordinates', 'Bitte näher heranzoomen, um den Fundort genau zu markieren.');
                document.getElementById('map')?.toggleAttribute('data-invalid', true);
                return;
            }
            this.setMarker(e.latlng.lat, e.latlng.lng);
        });

        const manLat = document.getElementById('manual-latitude');
        const manLng = document.getElementById('manual-longitude');
        [manLat, manLng].forEach(el => el?.addEventListener('change', () => {
            const [latMin, latMax] = this.coordinateRanges.latitude;
            const [lngMin, lngMax] = this.coordinateRanges.longitude;
            const lat = parseCoordinateInput(manLat?.value, latMin, latMax);
            const lng = parseCoordinateInput(manLng?.value, lngMin, lngMax);
            if (lat !== null && lng !== null) {
                this.setMarker(lat, lng);
                this.map.setView([lat, lng], this.map.getZoom());
            } else {
                this.clearCoordinates({ keepTypedText: true });
                const display = (value) => String(value).replace('.', ',');
                this.showError('coordinates', `Bitte gültige Koordinaten eingeben (Breitengrad: ${display(latMin)} bis ${display(latMax)}, Längengrad: ${display(lngMin)} bis ${display(lngMax)}).`);
            }
        }));

        const lat = parseFloat(document.getElementById('latitude')?.value);
        const lng = parseFloat(document.getElementById('longitude')?.value);
        if (coordinatesInRange(lat, lng, this.coordinateRanges)) {
            this.setMarker(lat, lng, false);
            this.map.setView([lat, lng], this.MIN_ZOOM);
        }
    },

    // Drops the marker together with the pair that would be submitted, so no
    // field is left claiming a position the map no longer shows. keepTypedText
    // spares the two visible inputs — the manual-entry handler runs on their
    // own change event, while the reporter is still filling the second one.
    clearCoordinates({ keepTypedText = false } = {}) {
        const fields = keepTypedText
            ? ['latitude', 'longitude']
            : ['latitude', 'longitude', 'manual-latitude', 'manual-longitude'];
        fields.forEach((id) => {
            const field = document.getElementById(id);
            if (field) field.value = '';
        });
        if (this.marker) { this.marker.remove(); this.marker = null; }
    },

    autoLocateIfNeeded() {
        const lat = parseCoordinateInput(document.getElementById('latitude')?.value, ...this.coordinateRanges.latitude);
        const lng = parseCoordinateInput(document.getElementById('longitude')?.value, ...this.coordinateRanges.longitude);
        if (lat === null || lng === null) {
            if (navigator.geolocation && this.locateCtrl && this.map) {
                this.locUpdates = 0;
                this.bestAccuracy = Infinity;
                this.locTimeout = null;
                this.locateCtrl.start();
            }
        }
    },

    handleLocationFound(e) {
        this.locUpdates += 1;
        const accuracy = e.accuracy || Infinity;

        if (accuracy < this.bestAccuracy || this.locUpdates === 1) {
            this.bestAccuracy = accuracy;
            // MIN_ZOOM, not 15: the message asks the user to click the map, and
            // clicking below MIN_ZOOM is refused.
            this.map.setView(e.latlng, this.MIN_ZOOM);

            let msg = '📍 GPS-Position gefunden';
            if (accuracy > 1000) msg += ' (ungefähr)';
            else if (accuracy > 100) msg += ` (ca. ${Math.round(accuracy)}m genau)`;
            else msg += ' (präzise)';
            msg += '. Bitte auf die Karte klicken, um den Fundort zu markieren.';
            this.showHint('coordinates', msg);
        }

        if (accuracy < 50 || this.locUpdates >= 5) {
            this.stopLocationUpdates();
        } else if (!this.locTimeout) {
            this.locTimeout = setTimeout(() => this.stopLocationUpdates(), 10000);
        }
    },

    stopLocationUpdates() {
        this.locateCtrl?.stop();
        if (this.locTimeout) { clearTimeout(this.locTimeout); this.locTimeout = null; }
    },

    // Out-of-range coordinates are dropped, never clamped: a clamped pair is a
    // valid-looking Fundort. The step-2 gate refuses to advance without one.
    setMarker(lat, lng, geocode = true) {
        if (!coordinatesInRange(lat, lng, this.coordinateRanges)) {
            this.clearCoordinates();
            this.showError('coordinates',
                'Dieser Punkt liegt außerhalb des Meldegebiets. '
                + 'Bitte markieren Sie den Fundort auf der Karte.');
            return;
        }

        if (this.marker) this.marker.setLatLng([lat, lng]);
        else {
            this.marker = L.marker([lat, lng], { draggable: true }).addTo(this.map)
                .on('dragend', (e) => this.setMarker(e.target.getLatLng().lat, e.target.getLatLng().lng));
        }

        const str = (n) => n.toFixed(6);
        document.getElementById('latitude').value = str(lat);
        document.getElementById('longitude').value = str(lng);
        const manLat = document.getElementById('manual-latitude');
        const manLng = document.getElementById('manual-longitude');
        if (manLat) manLat.value = str(lat);
        if (manLng) manLng.value = str(lng);

        this.clearError('coordinates');
        document.getElementById('map')?.toggleAttribute('data-invalid', false);
        if (geocode) this.reverseGeocode(lat, lng);
    },

    async reverseGeocode(lat, lng) {
        // Cancel any in-flight geocode request to prevent stale responses overwriting fresh data
        if (this.geocodeController) this.geocodeController.abort();
        this.geocodeController = new AbortController();
        const { signal } = this.geocodeController;

        const fields = {
            zip: document.getElementById('fund_zip_code'),
            city: document.getElementById('fund_city'),
            state: document.getElementById('fund_state'),
            district: document.getElementById('fund_district'),
            street: document.getElementById('fund_street')
        };
        // readOnly, not disabled: a disabled control is omitted from FormData, so
        // clicking "Weiter" mid-lookup would submit no city/state and fail
        // validation on fields that visibly hold a value.
        Object.values(fields).forEach(f => f && (f.readOnly = true));

        try {
            // Fetch Nominatim + local AGS lookup in parallel
            const [nominatimRes, agsRes] = await Promise.all([
                fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=de`, { signal }),
                fetch(`${this.agsUrl}?lat=${lat}&lon=${lng}`, { signal })
            ]);

            const a = (await nominatimRes.json()).address || {};
            const ags = agsRes.ok ? await agsRes.json() : {};

            if (fields.zip) fields.zip.value = a.postcode || '';
            if (fields.city) fields.city.value = a.city || a.town || a.village || '';
            if (fields.street) fields.street.value = a.house_number ? `${a.road || ''} ${a.house_number}`.trim() : (a.road || '');
            // AGS spatial data is authoritative for land/kreis; Nominatim as fallback
            if (fields.state) fields.state.value = ags.land || a.state || a.city || '';
            if (fields.district) fields.district.value = ags.kreis || a.county || a.borough || '';
        } catch (err) {
            if (err.name === 'AbortError') return; // superseded by a newer request
        } finally {
            Object.values(fields).forEach(f => f && (f.readOnly = false));
        }
    },

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (!overlay) return;
        overlay.classList.toggle('opacity-0', !show);
        overlay.classList.toggle('invisible', !show);
        overlay.classList.toggle('opacity-100', show);
    },

    setDropzoneLoading(show, msg = '') {
        const el = document.getElementById('dropzoneLoadingIndicator');
        const msgEl = document.getElementById('dropzoneLoadingMessage');
        if (el) el.hidden = !show;
        if (msgEl && msg) msgEl.textContent = msg;
    },

    showError(field, msg, focus = true) {
        const el = document.getElementById(`error-${field}`);
        if (!el) return;
        el.textContent = msg;
        el.classList.remove('is-hint');
        if (field === 'general') el.classList.remove('hidden');
        const input = document.getElementById(ERROR_INPUT[field] || field);
        if (input) {
            input.setAttribute('aria-invalid', 'true');
            input.setAttribute('aria-describedby', el.id);
            if (focus) input.focus();
        } else {
            el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    },

    // Advice, not a rejection: same slot, muted styling, and no focus steal —
    // focusing a text input here would pop the keyboard open on mobile.
    showHint(field, msg) {
        const el = document.getElementById(`error-${field}`);
        if (!el) return;
        el.textContent = msg;
        el.classList.add('is-hint');
    },

    clearError(field) {
        const el = document.getElementById(`error-${field}`);
        if (!el) return;
        el.textContent = '';
        el.classList.remove('is-hint');
        if (field === 'general') el.classList.add('hidden');
        const input = document.getElementById(ERROR_INPUT[field] || field);
        if (input) {
            input.removeAttribute('aria-invalid');
            input.removeAttribute('aria-describedby');
        }
    },

    clearErrors() {
        document.querySelectorAll('.field-error-message').forEach(el => el.textContent = '');
        document.querySelectorAll('[aria-invalid]').forEach(el => {
            el.removeAttribute('aria-invalid');
            el.removeAttribute('aria-describedby');
        });
        const gen = document.getElementById('error-general');
        if (gen) { gen.textContent = ''; gen.classList.add('hidden'); }
    }
};

document.addEventListener('DOMContentLoaded', () => ReportForm.init());
