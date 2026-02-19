// Admin modal module — HTMX-first rewrite
// JS only for: Leaflet map, marker placement, geocoding, clipboard, export, image modal

import { bindImageModal, syncDialogScrollLock } from './image-modal.js';

// ---------------------------------------------------------------------------
// State (map only — no more currentSightingId or isEditModeActive)
// ---------------------------------------------------------------------------
let map = null;
let marker = null;
let tempMarker = null;
let originalMarkerPosition = null;
let customIcon = null;
let geocodeRequestSeq = 0;

// Cached coordinate input references (invalidated when HTMX swaps destroy them)
let cachedCoordInputs = null;
function getCoordInputs() {
    if (!cachedCoordInputs || !document.contains(cachedCoordInputs.lat)) {
        cachedCoordInputs = {
            lat: document.querySelector('input[name="latitude"]'),
            lng: document.querySelector('input[name="longitude"]'),
        };
    }
    return cachedCoordInputs;
}

// ---------------------------------------------------------------------------
// Custom icon
// ---------------------------------------------------------------------------

function initializeCustomIcon() {
    customIcon = L.icon({
        iconUrl: '/static/images/map/marker-icon.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
    });
}

// ---------------------------------------------------------------------------
// Modal lifecycle (minimal — HTMX loads content)
// ---------------------------------------------------------------------------

function openModal() {
    var modal = document.getElementById('modal');
    if (!modal) return;
    var body = document.getElementById('modal-body');
    if (body) {
        body.innerHTML = '<div class="flex justify-center items-center h-full text-sm text-gray-500">'
            + 'Meldung wird geladen...'
            + '</div>';
    }
    if (!modal.open) modal.showModal();
    syncDialogScrollLock();
}

function closeModal() {
    var modal = document.getElementById('modal');
    if (modal && modal.open) modal.close();
    syncDialogScrollLock();
}

function showToast(message) {
    var toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 z-[9999] flex items-center gap-2 px-4 py-3 '
        + 'text-sm font-medium text-red-800 bg-red-100 rounded-lg border border-red-300 shadow-lg';
    toast.setAttribute('role', 'alert');
    toast.textContent = message;
    document.body.appendChild(toast);
    window.setTimeout(function () { toast.remove(); }, 4000);
}

// ---------------------------------------------------------------------------
// Map data from DOM
// ---------------------------------------------------------------------------

function getMapDataFromDOM() {
    var el = document.getElementById('map');
    if (!el) return null;
    return {
        latitude: el.dataset.lat,
        longitude: el.dataset.lng,
        strasse: el.dataset.strasse || '',
        plz: el.dataset.plz || '',
        ort: el.dataset.ort || '',
        kreis: el.dataset.kreis || '',
        land: el.dataset.land || '',
        editable: el.dataset.editable === 'true',
    };
}

// ---------------------------------------------------------------------------
// Map
// ---------------------------------------------------------------------------

function initiateMap(data) {
    requestAnimationFrame(function () {
        var lat = parseFloat(String(data.latitude).replace(',', '.'));
        var lng = parseFloat(String(data.longitude).replace(',', '.'));

        if (!customIcon) initializeCustomIcon();

        if (map) {
            map.remove();
            map = null;
            marker = null;
            tempMarker = null;
        }

        map = L.map('map', { zoomControl: false, tap: true }).setView([lat, lng], 13);

        map.createPane('tilePane');
        map.getPane('tilePane').style.zIndex = 200;
        map.createPane('markerPane');
        map.getPane('markerPane').style.zIndex = 400;
        map.createPane('popupPane');
        map.getPane('popupPane').style.zIndex = 600;

        var osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '\u00a9 OpenStreetMap contributors',
            maxZoom: 19, tileSize: 512, zoomOffset: -1, pane: 'tilePane',
        });

        var esriImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            minZoom: 0, maxZoom: 19, tileSize: 512, zoomOffset: -1,
            attribution: 'Tiles \u00a9 Esri', pane: 'tilePane',
        });

        var esriLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
            minZoom: 0, maxZoom: 19, tileSize: 512, zoomOffset: -1,
            attribution: 'Tiles \u00a9 Esri', pane: 'tilePane',
        });

        map.addLayer(osmLayer);
        L.control.layers({ 'Karte': osmLayer, 'Satellit': L.layerGroup([esriImagery, esriLabels]) }).addTo(map);

        marker = L.marker([lat, lng], { pane: 'markerPane', icon: customIcon }).addTo(map);

        var popupContent = buildPopupContent(lat, lng, data);
        marker.bindPopup(popupContent);

        L.control.zoom({ position: 'bottomright' }).addTo(map);

        // Second rAF: let browser settle layout before telling Leaflet the final size
        requestAnimationFrame(function () {
            map.invalidateSize();
        });

        if (!data.editable) {
            disableMapControls();
        }
    });
}

function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function buildPopupContent(lat, lng, data) {
    var e = escapeHtml;
    return `<div class="popup-content">
        <h2>${e(lat + ', ' + lng)}</h2>
        <ul class="popup-list">
            ${data.strasse ? `<li><strong>Straße:</strong> ${e(data.strasse)}</li>` : ''}
            ${data.plz ? `<li><strong>Postleitzahl:</strong> ${e(data.plz)}</li>` : ''}
            ${data.ort ? `<li><strong>Ort:</strong> ${e(data.ort)}</li>` : ''}
            ${data.kreis ? `<li><strong>Region:</strong> ${e(data.kreis)}</li>` : ''}
            ${data.land ? `<li><strong>Land:</strong> ${e(data.land)}</li>` : ''}
        </ul>
    </div>`;
}

function disableMapControls() {
    var btn = document.getElementById('markerPlacementBtn');
    if (btn) {
        btn.disabled = true;
        btn.classList.add('opacity-50', 'cursor-not-allowed');
        if (btn.classList.contains('bg-yellow-500')) cancelMarkerPlacement();
    }
}

// ---------------------------------------------------------------------------
// Marker placement
// ---------------------------------------------------------------------------

// Shared DOM refs + reset for marker placement UI
function getPlacementEls() {
    return {
        btn: document.getElementById('markerPlacementBtn'),
        btnText: document.getElementById('markerBtnText'),
        status: document.getElementById('placementStatus'),
        confirmBtns: document.getElementById('confirmationButtons'),
    };
}

function triggerCoordUpdate() {
    var coordForm = document.getElementById('coord-update-form');
    if (coordForm) coordForm.dispatchEvent(new CustomEvent('coord-valid'));
}

function resetPlacementUI(els) {
    els.btn.classList.remove('bg-yellow-500', 'hover:bg-yellow-600');
    els.btn.classList.add('bg-green-600', 'hover:bg-green-700');
    els.btnText.textContent = 'Marker platzieren';
    els.status.classList.add('hidden');
    els.confirmBtns.classList.add('hidden');
    map.off('click', onMapClick);
    map.getContainer().style.cursor = '';
}

function toggleMarkerPlacement() {
    var els = getPlacementEls();
    if (els.btn && els.btn.disabled) return;

    if (!els.btn.classList.contains('bg-yellow-500')) {
        originalMarkerPosition = marker.getLatLng();
        els.btn.classList.remove('bg-green-600', 'hover:bg-green-700');
        els.btn.classList.add('bg-yellow-500', 'hover:bg-yellow-600');
        els.btnText.textContent = 'Klicken Sie auf die Karte';
        els.status.classList.remove('hidden');
        map.on('click', onMapClick);
        map.getContainer().style.cursor = 'crosshair';
        map.once('click', function () { els.confirmBtns.classList.remove('hidden'); });
        marker.setOpacity(0.4);
    }
}

function confirmMarkerPlacement() {
    var els = getPlacementEls();

    if (tempMarker) {
        var pos = tempMarker.getLatLng();
        marker.setLatLng(pos);
        marker.setOpacity(1);

        var {lat: latInput, lng: lngInput} = getCoordInputs();
        if (latInput) latInput.value = pos.lat.toFixed(6);
        if (lngInput) lngInput.value = pos.lng.toFixed(6);

        // Dispatch coord-valid to trigger HTMX form submission
        triggerCoordUpdate();

        getAddressFromCoordinates(pos.lat, pos.lng);

        tempMarker.remove();
        tempMarker = null;
    }

    resetPlacementUI(els);
}

function cancelMarkerPlacement() {
    var els = getPlacementEls();

    if (tempMarker) {
        tempMarker.remove();
        tempMarker = null;
    }
    if (originalMarkerPosition) {
        marker.setLatLng(originalMarkerPosition);
        marker.setOpacity(1);
        var {lat: latInput, lng: lngInput} = getCoordInputs();
        if (latInput) latInput.value = originalMarkerPosition.lat.toFixed(6);
        if (lngInput) lngInput.value = originalMarkerPosition.lng.toFixed(6);
    }

    resetPlacementUI(els);
}

function onMapClick(e) {
    if (!customIcon) initializeCustomIcon();
    if (tempMarker) tempMarker.remove();

    tempMarker = L.marker(e.latlng, { pane: 'markerPane', icon: customIcon }).addTo(map);

    var {lat: latInput, lng: lngInput} = getCoordInputs();
    if (latInput) latInput.value = e.latlng.lat.toFixed(6);
    if (lngInput) lngInput.value = e.latlng.lng.toFixed(6);
}

function resetMarker(originalLat, originalLng) {
    var latLng = L.latLng(originalLat, originalLng);
    if (marker) {
        marker.setLatLng(latLng);
        map.setView(latLng, 13);
    }
    var {lat: latInput, lng: lngInput} = getCoordInputs();
    if (latInput) latInput.value = originalLat;
    if (lngInput) lngInput.value = originalLng;

    // Persist reset via HTMX coord form
    triggerCoordUpdate();
}

// ---------------------------------------------------------------------------
// Coordinate validation
// ---------------------------------------------------------------------------

function validateAndUpdateCoordinate(input, type) {
    var value = input.value.replace(',', '.');
    var num = parseFloat(value);

    var isValid = type === 'latitude'
        ? (!isNaN(num) && num >= -90 && num <= 90)
        : (!isNaN(num) && num >= -180 && num <= 180);

    if (isValid) {
        input.classList.remove('border-red-500');
        input.classList.add('border-gray-300');

        var {lat: latInput, lng: lngInput} = getCoordInputs();
        if (latInput.value && lngInput.value) {
            var lat = parseFloat(latInput.value.replace(',', '.'));
            var lng = parseFloat(lngInput.value.replace(',', '.'));
            if (!isNaN(lat) && !isNaN(lng)) {
                marker.setLatLng([lat, lng]);
                map.setView([lat, lng], map.getZoom());
                // Dispatch coord-valid to trigger HTMX form submission
                triggerCoordUpdate();
            }
        }
    } else {
        input.classList.remove('border-gray-300');
        input.classList.add('border-red-500');
    }
}

// ---------------------------------------------------------------------------
// Reverse geocoding
// ---------------------------------------------------------------------------

var ISO_TO_STATE = {
    'DE-BW': 'Baden-W\u00fcrttemberg', 'DE-BY': 'Bayern', 'DE-BE': 'Berlin',
    'DE-BB': 'Brandenburg', 'DE-HB': 'Bremen', 'DE-HH': 'Hamburg',
    'DE-HE': 'Hessen', 'DE-MV': 'Mecklenburg-Vorpommern', 'DE-NI': 'Niedersachsen',
    'DE-NW': 'Nordrhein-Westfalen', 'DE-RP': 'Rheinland-Pfalz', 'DE-SL': 'Saarland',
    'DE-SN': 'Sachsen', 'DE-ST': 'Sachsen-Anhalt', 'DE-SH': 'Schleswig-Holstein',
    'DE-TH': 'Th\u00fcringen',
};

function getStateNameFromISOCode(isoCode) {
    return ISO_TO_STATE[isoCode] || '';
}

function fetchAddressFromNominatim(latitude, longitude) {
    var url = new URL('https://nominatim.openstreetmap.org/reverse');
    url.searchParams.append('format', 'jsonv2');
    url.searchParams.append('lat', latitude.toString());
    url.searchParams.append('lon', longitude.toString());
    url.searchParams.append('zoom', '18');
    url.searchParams.append('addressdetails', '1');
    url.searchParams.append('extratags', '1');
    url.searchParams.append('namedetails', '1');
    url.searchParams.append('accept-language', 'de');
    return fetch(url.toString()).then(function (r) {
        if (!r.ok) throw new Error('HTTP error! status: ' + r.status);
        return r.json();
    });
}

function nominatimDelay() {
    // 1-second delay to respect Nominatim's usage policy
    return new Promise(function (resolve) {
        window.setTimeout(resolve, 1000);
    });
}

function getAddressFromCoordinates(latitude, longitude) {
    var requestSeq = ++geocodeRequestSeq;
    updateAddressDisplay({ street: 'Wird geladen...', zipCode: '', city: '', district: '', state: '' });

    nominatimDelay().then(function () {
        return fetchAddressFromNominatim(latitude, longitude);
    }).then(function (data) {
        if (requestSeq !== geocodeRequestSeq) return;

        if (data.error) {
            console.error('Nominatim API error:', data.error);
            updateAddressDisplay({ street: 'Adresse konnte nicht geladen werden', zipCode: '', city: '', district: '', state: '' });
            return;
        }

        var address = data.address || {};
        var district = address.county || address.city || '';
        var state = address.state || '';
        if (!state && data.extratags && data.extratags['ISO3166-2']) {
            state = getStateNameFromISOCode(data.extratags['ISO3166-2']);
        }

        var zipCode = address.postcode || '';
        var city = address.city || address.town || address.village || address.hamlet || '';
        var streetName = address.road || address.pedestrian || address.cycleway || address.path || address.footway || '';
        var houseNumber = address.house_number || '';
        var street = (streetName + ' ' + houseNumber).trim();

        updateAddressDisplay({
            street: street || 'Keine Stra\u00dfe gefunden',
            zipCode: zipCode,
            city: city || 'Kein Ort gefunden',
            district: district || 'Keine Region gefunden',
            state: state || 'Kein Land gefunden',
        });

        // Fill hidden address form and submit via HTMX
        var form = document.getElementById('address-update-form');
        if (form) {
            form.querySelector('[name="plz"]').value = zipCode;
            form.querySelector('[name="ort"]').value = city;
            form.querySelector('[name="strasse"]').value = street;
            form.querySelector('[name="kreis"]').value = district;
            form.querySelector('[name="land"]').value = state;
            form.requestSubmit();
        }

        // Update marker popup
        if (marker) {
            marker.setPopupContent(buildPopupContent(latitude, longitude, {
                strasse: street, plz: zipCode, ort: city, kreis: district, land: state,
            }));
        }

    }).catch(function (error) {
        if (requestSeq !== geocodeRequestSeq) return;
        console.error('Error fetching address data:', error);
        updateAddressDisplay({ street: 'Fehler beim Laden der Adresse', zipCode: '', city: '', district: '', state: '' });
    });
}

function setTextById(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
}

function updateAddressDisplay(d) {
    setTextById('addressStreet', d.street || 'Keine Stra\u00dfe');
    setTextById('addressCity', (d.zipCode || '') + ' ' + (d.city || 'Kein Ort'));
    setTextById('addressDistrict', d.district || 'Kein Kreis');
    setTextById('addressState', d.state || 'Kein Land');
}

// ---------------------------------------------------------------------------
// Sort / search / export
// ---------------------------------------------------------------------------

function setSortOrder(value) {
    var searchParams = new URLSearchParams(window.location.search);
    searchParams.set('sort_order', value);
    window.location.search = searchParams.toString();
}

function changeInputPattern() {
    var searchType = document.getElementById('searchType');
    var searchInput = document.getElementById('searchInput');
    if (!searchType || !searchInput) return;
    if (searchType.value === 'id') {
        searchInput.setAttribute('pattern', '\\d+');
        searchInput.setAttribute('title', 'Es sind nur IDs erlaubt.');
    } else {
        searchInput.removeAttribute('pattern');
        searchInput.removeAttribute('title');
    }
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.getElementById('searchInput').form.submit();
}

function exportData(exportType) {
    var urlParams = new URLSearchParams(window.location.search);
    var params = new URLSearchParams();
    ['statusInput', 'typeInput', 'q', 'search_type', 'dateFrom', 'dateTo', 'dateType'].forEach(function (param) {
        var value = urlParams.get(param);
        if (value !== null) params.append(param, value);
    });
    window.location.assign('/admin/export/xlsx/' + exportType + '?' + params.toString());
}

function setDateType(type) {
    // Update hidden inputs
    var dateTypeInput = document.getElementById('dateType');
    var hiddenDateType = document.getElementById('hiddenDateType');
    if (dateTypeInput) dateTypeInput.value = type;
    if (hiddenDateType) hiddenDateType.value = type;

    // Toggle active button styling
    document.querySelectorAll('.date-type-btn').forEach(function (btn) {
        var isActive = btn.dataset.dateType === type;
        btn.classList.toggle('bg-green-600', isActive);
        btn.classList.toggle('text-white', isActive);
        btn.classList.toggle('bg-white', !isActive);
        btn.classList.toggle('text-gray-600', !isActive);
        btn.classList.toggle('hover:bg-gray-100', !isActive);
        // Hide inner border when meld button is active
        if (btn.dataset.dateType === 'meld') {
            btn.classList.toggle('border-l-green-600', isActive);
        }
    });
}

// ---------------------------------------------------------------------------
// Flag overlay (modal image) — synced with footer checkbox toggles
// ---------------------------------------------------------------------------

function toggleModalOverlay() {
    var container = document.getElementById('modal-flag-overlay');
    if (!container) return;
    var unkl = document.getElementById('modal-overlay-unkl');
    var info = document.getElementById('modal-overlay-info');
    var unklChecked = document.querySelector('[data-flag="UNKL"]')?.checked;
    var infoChecked = document.querySelector('[data-flag="INFO"]')?.checked;
    if (unkl) unkl.classList.toggle('hidden', !unklChecked);
    if (info) info.classList.toggle('hidden', !infoChecked);
    container.classList.toggle('hidden', !unklChecked && !infoChecked);
}

// ---------------------------------------------------------------------------
// Clipboard
// ---------------------------------------------------------------------------

function copyUserId(userId, evt) {
    var button = evt.target.closest('button');
    if (!button) return;
    var svg = button.querySelector('svg');
    if (!svg) return;
    if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') {
        showToast('Clipboard wird vom Browser nicht unterstützt');
        return;
    }

    navigator.clipboard.writeText(userId).then(function () {
        var originalTitle = button.title;

        var checkPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        checkPath.setAttribute('stroke-linecap', 'round');
        checkPath.setAttribute('stroke-linejoin', 'round');
        checkPath.setAttribute('stroke-width', '2');
        checkPath.setAttribute('d', 'M5 13l4 4L19 7');
        while (svg.firstChild) svg.removeChild(svg.firstChild);
        svg.appendChild(checkPath);

        button.title = 'Kopiert!';
        button.classList.remove('text-gray-500');
        button.classList.add('text-green-600');

        window.setTimeout(function () {
            var copyPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            copyPath.setAttribute('stroke-linecap', 'round');
            copyPath.setAttribute('stroke-linejoin', 'round');
            copyPath.setAttribute('stroke-width', '2');
            copyPath.setAttribute('d', 'M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z');
            while (svg.firstChild) svg.removeChild(svg.firstChild);
            svg.appendChild(copyPath);
            button.title = originalTitle;
            button.classList.remove('text-green-600');
            button.classList.add('text-gray-500');
        }, 1500);
    }).catch(function (err) {
        console.error('Failed to copy user ID:', err);
        showToast('Fehler beim Kopieren der User ID');
    });
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

// Initialize map when location tab is settled via HTMX
// afterSettle fires after all OOB swaps + attribute settling are done
document.body.addEventListener('htmx:afterSettle', function (event) {
    if (event.detail.target?.id !== 'tab-content' && event.detail.target?.id !== 'modal-body') return;
    // Guard: don't initialize map if the dialog was closed while HTMX was in-flight
    var dialog = document.getElementById('modal');
    if (!dialog || !dialog.open) return;
    var mapEl = document.getElementById('map');
    if (mapEl) {
        var data = getMapDataFromDOM();
        if (data && data.latitude && data.longitude) {
            initiateMap(data);
        }
    }
});

window.addEventListener('load', function () {
    changeInputPattern();
});

document.addEventListener('DOMContentLoaded', function () {
    var editDialog = document.getElementById('modal');
    syncDialogScrollLock();
    bindImageModal();

    // Backdrop click-to-close (click on <dialog> itself = backdrop area)
    if (editDialog) {
        editDialog.addEventListener('click', function (e) {
            if (e.target === editDialog) closeModal();
        });
        // Map cleanup on any close (ESC, backdrop, button, HTMX after-request)
        editDialog.addEventListener('close', function () {
            geocodeRequestSeq += 1;
            if (map) { map.remove(); map = null; marker = null; tempMarker = null; }
            syncDialogScrollLock();
        });
    }

    var clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function () {
            var statusInput = document.getElementById('statusInput');
            var dateFromInput = document.getElementById('dateFrom');
            var dateToInput = document.getElementById('dateTo');
            var typeInput = document.getElementById('typeInput');
            if (statusInput) statusInput.value = 'all';
            if (dateFromInput) dateFromInput.value = '';
            if (dateToInput) dateToInput.value = '';
            if (typeInput) typeInput.value = 'all';
            setDateType('fund');
            if (statusInput) statusInput.closest('form').submit();
        });
    }
});

// ---------------------------------------------------------------------------
// Window exports (only functions referenced from template onclick handlers)
// ---------------------------------------------------------------------------
window.openModal = openModal;
window.closeModal = closeModal;
window.setSortOrder = setSortOrder;
window.clearSearch = clearSearch;
window.exportData = exportData;
window.changeInputPattern = changeInputPattern;
window.setDateType = setDateType;
window.validateAndUpdateCoordinate = validateAndUpdateCoordinate;
window.toggleMarkerPlacement = toggleMarkerPlacement;
window.confirmMarkerPlacement = confirmMarkerPlacement;
window.cancelMarkerPlacement = cancelMarkerPlacement;
window.resetMarker = resetMarker;
window.copyUserId = copyUserId;
window.toggleModalOverlay = toggleModalOverlay;
