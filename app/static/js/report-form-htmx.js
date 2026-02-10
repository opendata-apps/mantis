/**
 * HTMX Report Form - Minimal JS for photo/map handling
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-control-geocoder';
import 'leaflet-control-geocoder/dist/Control.Geocoder.css';
import 'leaflet.locatecontrol';
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css';
import EXIF from 'exif-js';
import htmx from 'htmx.org';

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

const ReportForm = {
    step: 0,
    map: null,
    marker: null,
    webpData: null,
    MIN_ZOOM: 17,

    init() {
        const form = document.getElementById('reportForm');
        if (!form) return;

        this.setupNav();
        this.setupPhoto();
        this.initMap();
        this.setupHtmx(form);
        this.showStep(0);
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

        if (i === 1 && this.map) {
            setTimeout(() => {
                this.map.invalidateSize();
                if (!document.getElementById('latitude')?.value) this.locateCtrl?.start();
            }, 100);
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
        });
    },

    loadReview() {
        const form = document.getElementById('reportForm');
        const data = new FormData(form);
        // photo_preview_data NOT sent - injected client-side via htmx:afterSwap
        htmx.ajax('POST', '/melden/htmx/review', {
            target: '#review-content-container',
            swap: 'innerHTML',
            values: Object.fromEntries(data)
        });
    },

    async submit(form) {
        if (!this.webpData?.blob) {
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
                headers: { 'X-CSRFToken': document.querySelector('input[name="csrf_token"]')?.value }
            });

            if (res.ok) {
                const json = await res.json().catch(() => ({}));
                window.location.href = json.redirect_url || '/success';
            } else throw new Error('Server error');
        } catch (err) {
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

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, minZoom: 3 })
            .addTo(this.map);

        if (L.Control.Geocoder) {
            L.Control.geocoder({ defaultMarkGeocode: false, placeholder: 'Adresse suchen...' })
                .on('markgeocode', (e) => {
                    // Auto-place marker when user searches for an address
                    this.map.setView(e.geocode.center, 15);
                    this.setMarker(e.geocode.center.lat, e.geocode.center.lng);
                })
                .addTo(this.map);
        }

        if (L.control.locate) {
            this.locateCtrl = L.control.locate({
                watch: false, setView: false, drawCircle: false, drawMarker: false, showPopup: false,
                strings: { title: 'Standort' }
            }).addTo(this.map);
            this.map.on('locationfound', (e) => {
                this.map.setView(e.latlng, 15);
                this.setMarker(e.latlng.lat, e.latlng.lng);
            });
        }

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
            }
        }));

        const lat = parseFloat(document.getElementById('latitude')?.value);
        const lng = parseFloat(document.getElementById('longitude')?.value);
        if (!isNaN(lat) && !isNaN(lng)) {
            this.setMarker(lat, lng, false);
            this.map.setView([lat, lng], 14);
        }
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
        const fields = {
            zip: document.getElementById('fund_zip_code'),
            city: document.getElementById('fund_city'),
            state: document.getElementById('fund_state'),
            district: document.getElementById('fund_district'),
            street: document.getElementById('fund_street')
        };
        Object.values(fields).forEach(f => f && (f.disabled = true));

        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=de`);
            const { address: a = {} } = await res.json();
            if (fields.zip) fields.zip.value = a.postcode || '';
            if (fields.city) fields.city.value = a.city || a.town || a.village || '';
            if (fields.state) fields.state.value = a.state || '';
            if (fields.district) fields.district.value = a.county || a.city || '';
            if (fields.street) fields.street.value = a.house_number ? `${a.road || ''} ${a.house_number}`.trim() : (a.road || '');
        } catch { } finally {
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
        if (el) el.textContent = msg;
    },

    clearError(field) {
        const el = document.getElementById(`error-${field}`);
        if (el) el.textContent = '';
    },

    clearErrors() {
        document.querySelectorAll('.field-error-message').forEach(el => el.textContent = '');
    }
};

document.addEventListener('DOMContentLoaded', () => ReportForm.init());
window.ReportForm = ReportForm;
