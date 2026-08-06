/**
 * HTMX Report Form - Minimal JS for photo/map handling
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-control-geocoder';
import 'leaflet-control-geocoder/dist/Control.Geocoder.css';
import { locate } from 'leaflet.locatecontrol';
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css';
import ExifReader from 'exifreader';
import htmx from 'htmx.org';
import { canvasIsBlank, extensionFor } from './image-checks.js';

// CSP hardening: disable eval-based attribute features (hx-on::*, `js:` prefix).
// The report form does not use them; this lets us drop `unsafe-eval` from CSP.
htmx.config.allowEval = false;

// Configure HTMX to include CSRF token in all requests
// This is the recommended approach from Flask-WTF documentation for AJAX requests
document.body.addEventListener('htmx:configRequest', (event) => {
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
    if (csrfToken) {
        event.detail.headers['X-CSRFToken'] = csrfToken;
    }
});

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconUrl: '/static/images/map/marker-icon.png',
    iconRetinaUrl: '/static/images/map/marker-icon-2x.png',
    shadowUrl: '/static/images/map/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});

window.L = L;
window.htmx = htmx;

const MIME_BY_EXT = {
    jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
    webp: 'image/webp', heic: 'image/heic', heif: 'image/heif'
};

const ReportForm = {
    step: 0,
    submitting: false,
    dirty: false,
    stepTitles: ['Foto & Details', 'Ort & Datum', 'Kontaktdaten', 'Überprüfen'],
    map: null,
    marker: null,
    webpData: null,
    geocodeController: null,
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
                e.returnValue = '';
            }
        });
        form.addEventListener('input', () => { this.dirty = true; });
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
            s.classList.toggle('active', idx === i);
        });
        this.step = i;

        document.title = `${this.stepTitles[i]} – Sichtung melden`;

        // Move focus to the new step's heading (skip on initial load to avoid jarring scroll)
        if (this._initialized) {
            const heading = steps[i].querySelector('h3');
            if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus(); }
        }
        this._initialized = true;

        if (i === 1 && this.map) {
            // Allow layout to settle before resizing map + auto-locating
            const activateMap = () => {
                this.map.invalidateSize();
                this.autoLocateIfNeeded();
            };
            setTimeout(activateMap, 100);
        }
        if (i === 3) this.loadReview();
    },

    setupHtmx(form) {
        document.body.addEventListener('htmx:beforeRequest', (e) => {
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
        // Map error container IDs to their user-facing input IDs
        const errorToInput = { coordinates: 'manual-latitude' };
        let firstInvalid = null;

        document.querySelectorAll('.field-error-message').forEach(el => {
            const field = el.id.replace('error-', '');
            const inputId = errorToInput[field] || field;
            const input = document.getElementById(inputId);
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
        // photo_preview_data NOT sent - injected client-side via htmx:afterSwap
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
            const ext = extensionFor(this.webpData.blob.type);
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
                throw new Error(json?.error || 'Server error');
            }

            this.dirty = false;
            window.location.href = json.redirect_url;
        } catch (err) {
            this.submitting = false;
            this.showLoading(false);
            this.showError('general', err.message);
        }
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
        document.getElementById('remove-photo')?.addEventListener('click', () => this.removePhoto());
    },

    async handlePhoto(file) {
        if (!file) return;
        const type = this.imageType(file);
        if (!type) return this.showError('photo', 'Ungültiges Bildformat.');
        if (file.size > 12 * 1024 * 1024) return this.showError('photo', 'Max 12MB.');

        this.clearError('photo');
        this.setDropzoneLoading(true, 'Bild wird verarbeitet...');

        // Start the read here, still inside the change event's own task: Android
        // hands gallery items over as proxy content:// URIs that can turn
        // unreadable moments later.
        const read = file.arrayBuffer();
        let exif = {};

        try {
            const bytes = await this.stage('read', read);
            exif = await this.extractExif(bytes);
            const webp = await this.toWebp(bytes, type, file.size);
            this.setPhoto(webp.blob, webp.dataUrl, file.name);
        } catch (err) {
            const escalation = await this.reportPhotoFailure(file, err);

            // Converting in the browser is an optimisation, not a requirement —
            // the server decodes every format this form accepts. Forwarding the
            // original costs bandwidth; refusing it costs the sighting. The one
            // exception is a 'read' failure: those bytes were never accessible,
            // so forwarding the file would just defer the same failure to
            // submit — after four steps of work — as a misleading connection error.
            if (err.stage === 'read') {
                // Reset before showing: removePhoto() clears the photo error, so
                // the other order erases the message the user needs to see.
                this.removePhoto();
                // Never "try again": across 67 logged read failures on only 39
                // distinct files, re-picking the same photo failed every time
                // (100% Android). The bytes are not on the device — typically a
                // cloud-only gallery entry — so the only advice that works is to
                // download it first or pick a different photo.
                this.showError('photo',
                    'Dieses Foto konnte nicht vom Gerät gelesen werden — meist liegt es nur '
                    + 'in der Cloud (z. B. Google Fotos). Bitte laden Sie es in der Galerie '
                    + 'herunter oder wählen Sie ein anderes Foto.');
                this.showEscalation(escalation);
                return;
            }

            this.setPhoto(file, URL.createObjectURL(file), file.name);
            this.showHint('photo',
                'Das Foto konnte im Browser nicht verkleinert werden und wird unverändert '
                + 'hochgeladen — das kann etwas länger dauern.');
        } finally {
            this.setDropzoneLoading(false);
        }

        this.applyExif(exif);
    },

    // The converted blob and the untouched original are shown and submitted the
    // same way; only the preview source differs (data: URL vs blob: URL).
    setPhoto(blob, previewSrc, fileName) {
        this.hideEscalation();
        this.releasePreview();
        this.webpData = { previewSrc, blob, fileName };
        this.dirty = true;

        document.getElementById('photo-upload-area')?.classList.add('hidden');
        const preview = document.getElementById('photoPreview');
        const img = document.getElementById('preview-img');
        if (preview && img) {
            preview.classList.remove('hidden');
            img.src = previewSrc;
        }
    },

    // A blob: URL pins the whole original in memory until it is revoked.
    releasePreview() {
        if (this.webpData?.previewSrc?.startsWith('blob:')) {
            URL.revokeObjectURL(this.webpData.previewSrc);
        }
    },

    // Android pickers sometimes deliver a File with an empty `type`, so the
    // extension has to be able to stand in for it — and vice versa.
    imageType(file) {
        const ext = (file.name || '').toLowerCase().split('.').pop();
        const type = (file.type || '').toLowerCase();
        if (Object.values(MIME_BY_EXT).includes(type)) return type;
        return MIME_BY_EXT[ext] || null;
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

    // Chrome froze the Android UA at "Android 10; K" for every device, so the
    // log cannot tell a Samsung from a Pixel — and which picker hands Chrome the
    // content:// URI depends on exactly that. Client hints are the only way to
    // ask; the JS API needs no Accept-CH opt-in.
    async deviceHints() {
        try {
            const hints = await navigator.userAgentData?.getHighEntropyValues?.(
                ['model', 'platformVersion']);
            return { model: hints?.model || '', osVersion: hints?.platformVersion || '' };
        } catch {
            return {};
        }
    },

    // The Android photo picker hands over a synthesised numeric name
    // (168243243.jpg) where DocumentsUI passes the gallery's own
    // (IMG_20260803_101112.jpg) — the shape is the only clue in the browser to
    // which picker produced the file. The name itself can identify a person, so
    // only the class travels.
    nameShape(name) {
        const base = (name || '').replace(/\.[^.]*$/, '');
        if (!base) return 'empty';
        return /^\d+$/.test(base) ? 'numeric' : 'named';
    },

    // The conversion runs entirely in the browser, so until now a failure here
    // was invisible to the project — the report was simply never submitted.
    // Reports the failing step and the file class, never the image itself.
    // Resolves to the server's escalation payload once it has counted enough
    // failures for this session, otherwise null (204).
    async reportPhotoFailure(file, err) {
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
                    model: hints.model || '',
                    osVersion: hints.osVersion || ''
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

    extractExif(bytes) {
        // EXIF autofill is a non-essential enhancement; it must never block or freeze
        // the upload. Time-box it and swallow every failure (degrade to no autofill).
        // ExifReader returns tags synchronously for an ArrayBuffer (a promise only for
        // a File), so the parse has to be lifted into one before it can be raced.
        const parse = Promise.resolve()
            .then(() => ExifReader.load(bytes, { expanded: true }))
            .then((tags) => {
                const dateTime = tags.exif?.DateTimeOriginal?.description || tags.exif?.DateTime?.description;
                const gps = (typeof tags.gps?.Latitude === 'number' && typeof tags.gps?.Longitude === 'number')
                    ? { lat: tags.gps.Latitude, lng: tags.gps.Longitude }
                    : null;
                return { dateTime, gps };
            })
            .catch(() => ({}));
        const timeout = new Promise((resolve) => setTimeout(() => resolve({}), 3000));
        return Promise.race([parse, timeout]);
    },

    // An object URL, not a data URL: base64 inflates a 6MB photo into an 8MB
    // string handed to img.src, four times Chromium's 2MB URL ceiling, and it
    // keeps that string in memory next to the decoded bitmap.
    decode(blob) {
        const url = URL.createObjectURL(blob);
        return new Promise((res, rej) => {
            const el = new Image();
            el.onload = () => res(el);
            el.onerror = () => rej(new Error('image decode failed'));
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

        const maxDim = /Mobile|Android|iPhone|iPad/i.test(navigator.userAgent) ? 2048 : 4096;
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

        // drawImage can no-op without throwing in an Android WebView, which
        // encodes a full-size but entirely transparent frame. Seven such reports
        // reached the archive before this check existed — one of them approved —
        // so verify the draw actually landed. Outside the catch above: this is a
        // verdict, not a native fault, and must keep its own label.
        if (canvasIsBlank(ctx, w, h)) throw this.photoError('blank-canvas');

        const sizeMB = size / 1048576;
        const pixels = w * h;
        let q = sizeMB > 10 ? 0.6 : sizeMB > 5 ? 0.7 : 0.8;
        if (pixels > 8e6) q = Math.min(q, 0.6);
        else if (pixels > 4e6) q = Math.min(q, 0.7);

        const encode = (mime) => new Promise((r) => canvas.toBlob(r, mime, q));
        // WebKit (incl. iOS 26) cannot encode WebP via canvas: toBlob returns null
        // or silently falls back to PNG. Fall back to JPEG, which every engine encodes
        // and the server (PIL) decodes — unlike HEIC. See WebKit regression 89356ad.
        let mime = 'image/webp';
        let out = await encode(mime);
        if (!out || out.type !== mime) {
            mime = 'image/jpeg';
            out = await encode(mime);
        }
        if (!out) throw this.photoError('encode');

        const dataUrl = canvas.toDataURL(mime, q);
        // WebKit only frees a canvas once it is resized away (bug 195325), and on
        // a phone this is the largest allocation the form makes.
        canvas.width = canvas.height = 0;
        return { blob: out, dataUrl };
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

        if (gps) {
            const { lat, lng } = gps;
            document.getElementById('latitude').value = lat;
            document.getElementById('longitude').value = lng;
            const manLat = document.getElementById('manual-latitude');
            const manLng = document.getElementById('manual-longitude');
            if (manLat) manLat.value = lat.toFixed(6);
            if (manLng) manLng.value = lng.toFixed(6);
            document.getElementById('exif-location')?.textContent &&
                (document.getElementById('exif-location').textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`);

            if (this.map) {
                setTimeout(() => {
                    this.map.invalidateSize();
                    this.map.setView([lat, lng], 14);
                    this.setMarker(lat, lng, true);
                }, 100);
            }
            hasData = true;
        }

        if (hasData) document.getElementById('exif-data')?.classList.remove('hidden');
    },

    initMap() {
        const container = document.getElementById('map');
        if (!container) return;

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

        if (L.Control.Geocoder) {
            L.Control.geocoder({ defaultMarkGeocode: false, placeholder: 'Adresse suchen...' })
                .on('markgeocode', (e) => {
                    // Auto-place marker when user searches for an address
                    this.map.setView(e.geocode.center, 15);
                    this.setMarker(e.geocode.center.lat, e.geocode.center.lng);
                })
                .addTo(this.map);
        }

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
                document.getElementById('map')?.classList.add('invalid');
                return;
            }
            this.setMarker(e.latlng.lat, e.latlng.lng);
        });

        const manLat = document.getElementById('manual-latitude');
        const manLng = document.getElementById('manual-longitude');
        [manLat, manLng].forEach(el => el?.addEventListener('change', () => {
            const lat = parseFloat(manLat?.value), lng = parseFloat(manLng?.value);
            if (!isNaN(lat) && !isNaN(lng) && lat >= 30 && lat <= 60 && lng >= -20 && lng <= 30) {
                this.setMarker(lat, lng);
                this.map.setView([lat, lng], this.map.getZoom());
            } else {
                document.getElementById('latitude').value = '';
                document.getElementById('longitude').value = '';
                if (this.marker) { this.marker.remove(); this.marker = null; }
                this.showError('coordinates', 'Bitte gültige Koordinaten eingeben (Breitengrad: 30 bis 60, Längengrad: -20 bis 30).');
            }
        }));

        const lat = parseFloat(document.getElementById('latitude')?.value);
        const lng = parseFloat(document.getElementById('longitude')?.value);
        if (!isNaN(lat) && !isNaN(lng)) {
            this.setMarker(lat, lng, false);
            this.map.setView([lat, lng], 14);
        }
    },

    autoLocateIfNeeded() {
        const lat = parseFloat(document.getElementById('latitude')?.value);
        const lng = parseFloat(document.getElementById('longitude')?.value);
        if (isNaN(lat) || isNaN(lng)) {
            if (navigator.geolocation && this.locateCtrl && this.map) {
                this._locUpdates = 0;
                this._bestAccuracy = Infinity;
                this._locTimeout = null;
                this.locateCtrl.start();
            }
        }
    },

    handleLocationFound(e) {
        this._locUpdates = (this._locUpdates || 0) + 1;
        const accuracy = e.accuracy || Infinity;

        if (accuracy < this._bestAccuracy || this._locUpdates === 1) {
            this._bestAccuracy = accuracy;
            this.map.setView(e.latlng, 15);

            let msg = '📍 GPS-Position gefunden';
            if (accuracy > 1000) msg += ' (ungefähr)';
            else if (accuracy > 100) msg += ` (ca. ${Math.round(accuracy)}m genau)`;
            else msg += ' (präzise)';
            msg += '. Bitte auf die Karte klicken, um den Fundort zu markieren.';
            this.showError('coordinates', msg);
        }

        if (accuracy < 50 || this._locUpdates >= 5) {
            this.stopLocationUpdates();
        } else if (!this._locTimeout) {
            this._locTimeout = setTimeout(() => this.stopLocationUpdates(), 10000);
        }
    },

    stopLocationUpdates() {
        this.locateCtrl?.stop();
        if (this._locTimeout) { clearTimeout(this._locTimeout); this._locTimeout = null; }
    },

    setMarker(lat, lng, geocode = true) {
        lat = Math.max(30, Math.min(60, lat));
        lng = Math.max(-20, Math.min(30, lng));

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
        document.getElementById('map')?.classList.remove('invalid');
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
        Object.values(fields).forEach(f => f && (f.disabled = true));

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
            Object.values(fields).forEach(f => f && (f.disabled = false));
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
        if (el) el.classList.toggle('hidden', !show);
        if (msgEl && msg) msgEl.textContent = msg;
    },

    showError(field, msg) {
        const el = document.getElementById(`error-${field}`);
        if (!el) return;
        el.textContent = msg;
        el.classList.remove('is-hint');
        if (field === 'general') el.classList.remove('hidden');
        const errorToInput = { coordinates: 'manual-latitude' };
        const input = document.getElementById(errorToInput[field] || field);
        if (input) {
            input.setAttribute('aria-invalid', 'true');
            input.setAttribute('aria-describedby', el.id);
            input.focus();
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
        const errorToInput = { coordinates: 'manual-latitude' };
        const input = document.getElementById(errorToInput[field] || field);
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
window.ReportForm = ReportForm;
