// Street map and satellite view of the map page and the report form.
import L from 'leaflet';

// Leaflet labels its controls in English. The zoom titles are options; the
// layers toggle gets its title in Control.Layers' own layout code, so it is
// replaced once the control is on the map.
L.Control.Zoom.mergeOptions({ zoomInTitle: 'Vergrößern', zoomOutTitle: 'Verkleinern' });

export function addBaseLayers(map, tileOptions = {}) {
    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        ...tileOptions,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    });
    const esri = (service) => L.tileLayer(
        `https://server.arcgisonline.com/ArcGIS/rest/services/${service}/MapServer/tile/{z}/{y}/{x}`,
        { ...tileOptions, attribution: 'Tiles &copy; Esri' },
    );

    map.addLayer(osm);
    const layers = L.control.layers({
        'Karte': osm,
        'Satellit': L.layerGroup([esri('World_Imagery'), esri('Reference/World_Boundaries_and_Places')]),
    }).addTo(map);
    layers.getContainer().querySelector('.leaflet-control-layers-toggle').title = 'Kartenebenen';
}
