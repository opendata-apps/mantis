// Auswertungen map page: year selector, marker clusters and popups
import L from 'leaflet';
import './map.js';

const { pointsUrl, years, selectedYear, markerIcon } = JSON.parse(
  document.getElementById('map-data').textContent
);
// Year selector control
L.Control.YearSelector = L.Control.extend({
  onAdd: function () {
    var div = L.DomUtil.create('div', 'leaflet-control leaflet-bar');
    var select = L.DomUtil.create('select', 'year-selector', div);
    select.id = 'yearSelect';
    select.setAttribute('aria-label', 'Jahr der Sichtungen auswählen');

    var option = L.DomUtil.create('option', '', select);
    option.value = '';
    option.innerHTML = 'Alle Jahre';
    if (!selectedYear) option.selected = true;

    years.forEach(function (year) {
      var opt = L.DomUtil.create('option', '', select);
      opt.value = String(year);
      opt.innerHTML = String(year);
      if (selectedYear === year) opt.selected = true;
    });

    L.DomEvent.on(select, 'change', e => {
      const v = e.target.value;
      window.location.href = v ? `/auswertungen?year=${v}` : '/auswertungen';
    });
    return div;
  }
});
L.control.yearSelector = opts => new L.Control.YearSelector(opts);

// Init map
// maxZoom 12 is the second half of obfuscate_location() in routes/data.py:
// markers are offset by up to ~500 m, and this keeps the map from being
// zoomed in far enough for that offset to stand out. The report form and the
// reviewer modal deliberately go to 18 and 19 — they show the real point.
const germanyBounds = [[47.270111, 5.866342], [55.058347, 15.041896]];
const map = L.map('map', {
  renderer: L.canvas(),
  maxBounds: germanyBounds,
  maxBoundsViscosity: 1.0,
  keyboard: true,
  keyboardPanDelta: 100,
  minZoom: 6,
  maxZoom: 12,
  zoomControl: false
}).setView([51.991649, 13.080113], 9);

const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
});
const esriImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  attribution: 'Tiles &copy; Esri'
});
const esriLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
  attribution: 'Tiles &copy; Esri'
});

map.addLayer(osmLayer);
L.control.layers({ 'Karte': osmLayer, 'Satellit': L.layerGroup([esriImagery, esriLabels]) }).addTo(map);
L.control.yearSelector({ position: 'topleft' }).addTo(map);
L.control.zoom({ position: 'topleft' }).addTo(map);

// Cluster legend
L.Control.ClusterLegend = L.Control.extend({
  onAdd: function () {
    var div = L.DomUtil.create('div', 'cluster-legend leaflet-bar');
    div.innerHTML =
      '<span class="cluster-legend-item"><span class="cluster-dot cluster-dot--small"></span> &lt; 10</span>' +
      '<span class="cluster-legend-item"><span class="cluster-dot cluster-dot--medium"></span> 10 – 99</span>' +
      '<span class="cluster-legend-item"><span class="cluster-dot cluster-dot--large"></span> 100 +</span>';
    return div;
  }
});
new L.Control.ClusterLegend({ position: 'bottomright' }).addTo(map);

// Markers: one click handler on the group instead of a popup per marker
const markers = L.markerClusterGroup({ showCoverageOnHover: false, chunkedLoading: true });
const customIcon = L.icon({
  iconUrl: markerIcon,
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34]
});

// A bound popup opens itself on click; this only fills it, retrying after errors.
const loaded = new WeakSet();
markers.on('click', e => {
  const marker = e.layer;
  if (loaded.has(marker)) return;
  const loading = "<div class='popup-loading'>Daten werden geladen...</div>";
  if (marker.getPopup()) marker.setPopupContent(loading);
  else marker.bindPopup(loading).openPopup();
  fetch(`/get_marker_data/${marker.options.reportId}`)
    .then(res => {
      if (!res.ok) throw new Error(res.status);
      return res.text();
    })
    .then(html => {
      marker.setPopupContent(html);
      loaded.add(marker);
    })
    .catch(() => marker.setPopupContent("<div class='popup-error'>Fehler beim Laden.</div>"));
});
map.addLayer(markers);

fetch(pointsUrl)
  .then(res => {
    if (!res.ok) throw new Error(res.status);
    return res.json();
  })
  .then(points => markers.addLayers(points.map(([reportId, lat, lon]) =>
    L.marker([lat, lon], { icon: customIcon, reportId }))));
