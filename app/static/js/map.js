// Leaflet with marker clusters for the map page and the reviewer page.
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import '../css/map.css';

// Fix default icon paths
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

// admin-modal.js does not import Leaflet; it uses this global.
window.L = L;
