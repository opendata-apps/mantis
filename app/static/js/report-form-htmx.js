/**
 * HTMX Report Form - Minimal JS for photo/map handling
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-control-geocoder';
import 'leaflet-control-geocoder/dist/Control.Geocoder.css';
import { locate } from 'leaflet.locatecontrol';
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css';
import EXIF from 'exif-js';
import htmx from 'htmx.org';

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
window.EXIF = EXIF;
window.htmx = htmx;

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
                if (img && this.webpData?.dataUrl) {
                    img.src = this.webpData.dataUrl;
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

            const hasError = el.textContent.trim().length > 0;
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
            const name = (this.webpData.fileName || 'photo.webp').replace(/\.[^.]+$/, '.webp');
            data.append('photo', new File([this.webpData.blob], name, { type: 'image/webp' }));

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
        dropzone.addEventListener('click', () => input.click());
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
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];
        const ext = file.name.toLowerCase().split('.').pop();
        if (!validTypes.includes(file.type.toLowerCase()) && !['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'].includes(ext)) {
            return this.showError('photo', 'Ungültiges Bildformat.');
        }
        if (file.size > 12 * 1024 * 1024) return this.showError('photo', 'Max 12MB.');

        this.clearError('photo');
        this.setDropzoneLoading(true, 'Bild wird verarbeitet...');

        try {
            const exif = await this.extractExif(file);
            const webp = await this.toWebp(file);

            this.webpData = { dataUrl: webp.dataUrl, blob: webp.blob, fileName: file.name };
            this.dirty = true;

            document.getElementById('photo-upload-area')?.classList.add('hidden');
            const preview = document.getElementById('photoPreview');
            const img = document.getElementById('preview-img');
            if (preview && img) {
                preview.classList.remove('hidden');
                img.src = webp.dataUrl;
            }

            this.applyExif(exif);
        } catch (err) {
            this.showError('photo', 'Fehler bei der Bildverarbeitung.');
            this.removePhoto();
        } finally {
            this.setDropzoneLoading(false);
        }
    },

    extractExif(file) {
        return new Promise((resolve) => {
            const timeout = setTimeout(() => resolve({}), 5000);
            try {
                EXIF.getData(file, function () {
                    clearTimeout(timeout);
                    const dt = EXIF.getTag(this, 'DateTimeOriginal') || EXIF.getTag(this, 'DateTime');
                    const lat = EXIF.getTag(this, 'GPSLatitude');
                    const lng = EXIF.getTag(this, 'GPSLongitude');
                    const latRef = EXIF.getTag(this, 'GPSLatitudeRef');
                    const lngRef = EXIF.getTag(this, 'GPSLongitudeRef');

                    let gps = null;
                    if (lat && lng && latRef && lngRef) {
                        const toDec = (dms, ref) => {
                            let dd = dms[0] + dms[1] / 60 + dms[2] / 3600;
                            return (ref === 'S' || ref === 'W') ? -dd : dd;
                        };
                        gps = { lat: toDec(lat, latRef), lng: toDec(lng, lngRef) };
                    }
                    resolve({ dateTime: dt, gps });
                });
            } catch { clearTimeout(timeout); resolve({}); }
        });
    },

    async toWebp(file) {
        const isHeic = file.type.includes('heic') || file.type.includes('heif');

        const loadImg = (src) => new Promise((res, rej) => {
            const img = new Image();
            img.onload = () => res(img);
            img.onerror = rej;
            img.src = src;
        });

        let imgSrc;
        if (isHeic) {
            const { default: heic2any } = await import('heic2any');
            const converted = await heic2any({ blob: file, toType: 'image/jpeg', quality: 0.85 });
            imgSrc = URL.createObjectURL(converted);
        } else {
            imgSrc = await new Promise((res, rej) => {
                const r = new FileReader();
                r.onload = (e) => res(e.target.result);
                r.onerror = rej;
                r.readAsDataURL(file);
            });
        }

        const img = await loadImg(imgSrc);
        if (isHeic) URL.revokeObjectURL(imgSrc);

        const maxDim = /Mobile|Android|iPhone|iPad/i.test(navigator.userAgent) ? 2048 : 4096;
        let w = img.naturalWidth, h = img.naturalHeight;
        if (w > maxDim || h > maxDim) {
            const ratio = w / h;
            if (w > h) { w = maxDim; h = Math.round(maxDim / ratio); }
            else { h = maxDim; w = Math.round(maxDim * ratio); }
        }

        const canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        canvas.getContext('2d').drawImage(img, 0, 0, w, h);

        const sizeMB = file.size / 1048576;
        const pixels = w * h;
        let q = sizeMB > 10 ? 0.6 : sizeMB > 5 ? 0.7 : 0.8;
        if (pixels > 8e6) q = Math.min(q, 0.6);
        else if (pixels > 4e6) q = Math.min(q, 0.7);

        return new Promise((res, rej) => {
            canvas.toBlob((blob) => {
                if (!blob) return rej(new Error('Conversion failed'));
                res({ blob, dataUrl: canvas.toDataURL('image/webp', q) });
            }, 'image/webp', q);
        });
    },

    removePhoto() {
        const input = document.getElementById('photo');
        if (input) input.value = '';
        document.getElementById('photoPreview')?.classList.add('hidden');
        document.getElementById('exif-data')?.classList.add('hidden');
        document.getElementById('photo-upload-area')?.classList.remove('hidden');
        const img = document.getElementById('preview-img');
        if (img) img.src = '';
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
            if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
                this.setMarker(lat, lng);
                this.map.setView([lat, lng], this.map.getZoom());
            } else {
                document.getElementById('latitude').value = '';
                document.getElementById('longitude').value = '';
                if (this.marker) { this.marker.remove(); this.marker = null; }
                this.showError('coordinates', 'Bitte gültige Koordinaten eingeben (Breitengrad: -90 bis 90, Längengrad: -180 bis 180).');
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
        lat = Math.max(-90, Math.min(90, lat));
        lng = Math.max(-180, Math.min(180, lng));

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

    clearError(field) {
        const el = document.getElementById(`error-${field}`);
        if (!el) return;
        el.textContent = '';
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
