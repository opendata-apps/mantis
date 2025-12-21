/**
 * Report Form bundle - all JS for the sighting report form
 * Combines libraries + application code into one bundle
 */

// === Libraries ===
// Leaflet + plugins
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-control-geocoder';
import 'leaflet-control-geocoder/dist/Control.Geocoder.css';
import 'leaflet.locatecontrol';
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css';

// Use custom marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconUrl: '/static/images/map/marker-icon.png',
    iconRetinaUrl: '/static/images/map/marker-icon-2x.png',
    shadowUrl: '/static/images/map/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

window.L = L;

// EXIF handling (heic2any lazy-loaded in webp_converter.js when needed)
import EXIF from 'exif-js';
window.EXIF = EXIF;

// === Application Code ===
import './webp_converter.js';
import './exif_handler.js';
import './form_helpers.js';
import './photo_handler.js';
import './german_administrative_divisions.js';
import './map_handler.js';
import './report_form_app.js';
