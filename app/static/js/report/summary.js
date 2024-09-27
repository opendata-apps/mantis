let summaryMap;
let summaryMarker;
let summaryMarkerPopup;

const SUMMARY_FIELDS = [
  'summaryLongitude', 'summaryLatitude', 'summaryStreet', 'summaryZipCode',
  'summaryCity', 'summaryDistrict', 'summaryState', 'summaryGender',
  'summaryPictureDescription', 'summaryFirstName', 'summaryLastName',
  'summarySightingDate', 'summaryContact', 'summaryBildbeschreibung'
];

const KEY_MAP = {
  'firstname': 'report_first_name',
  'lastname': 'report_last_name',
  'sightingdate': 'sighting_date',
  'contact': 'contact',
  'bildbeschreibung': 'picture_description',
  'picturedescription': 'picture_description',
  'zipcode': 'zip_code'
};

function initSummaryMap() {
  if (summaryMap) {
    return; // Map already initialized
  }

  summaryMap = L.map("summaryMap", {
    minZoom: 5,
    maxBoundsViscosity: 1.0
  }).setView([52.5200, 13.4050], 7);

  const openStreetMapLayerSummary = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
    maxZoom: 18,
  });

  const arcGISLayerSummary = L.esri.Vector.vectorBasemapLayer("ArcGIS:Imagery", {
    apikey: mapApiKey
  });

  summaryMap.addLayer(openStreetMapLayerSummary);

  const baseMapsSummary = {
    "OpenStreetMap": openStreetMapLayerSummary,
    "ArcGIS": arcGISLayerSummary
  };

  L.control.layers(baseMapsSummary).addTo(summaryMap);

  summaryMarker = L.marker([0, 0]).addTo(summaryMap);
  summaryMarkerPopup = L.popup().setContent("");
  summaryMarker.bindPopup(summaryMarkerPopup);
}

const updateSummary = debounce(() => {
  if (!summaryMap || !summaryMarker) {
    initSummaryMap();
  }

  const storedData = getLocalStorageWithExpiry('formData');

  if (storedData) {
    try {
      const data = JSON.parse(storedData);
      updateSummaryMap(data);
      updateSummaryImage();
      updateSummaryFields(data);
    } catch (e) {
      console.error('Error parsing stored form data in updateSummary:', e);
      // Optionally, display an error message to the user
    }
  }
}, 300);

function updateSummaryMap(data) {
  if (data.latitude && data.longitude) {
    const newLatLng = new L.LatLng(data.latitude, data.longitude);
    summaryMarker.setLatLng(newLatLng);
    summaryMap.setView(newLatLng, 13);

    requestAnimationFrame(() => {
      summaryMap.invalidateSize();
    });

    const popupContent = generatePopupContent(data);
    summaryMarkerPopup.setContent(popupContent);
  }
}

function generatePopupContent(data) {
  return `
    <strong>Straße:</strong> ${data.street ?? ''}<br>
    <strong>Postleitzahl:</strong> ${data.zip_code ?? ''}<br>
    <strong>Ort:</strong> ${data.city ?? ''}<br>
    <strong>Landkreis/Stadt:</strong> ${data.district ?? ''}<br>
    <strong>Bundesland:</strong> ${data.state ?? ''}
  `;
}

function updateSummaryImage() {
  const pictureInput = document.getElementById('picture');
  const file = pictureInput?.files[0];
  const summaryImage = document.getElementById('summaryImage');

  if (file) {
    const reader = new FileReader();
    reader.onload = function () {
      summaryImage.src = reader.result;
    };
    reader.readAsDataURL(file);
  } else {
    summaryImage.src = '#';
  }
}

function updateSummaryFields(data) {
  if (typeof data !== 'object' || data === null) {
    console.error('Invalid data object');
    return;
  }

  SUMMARY_FIELDS.forEach(field => {
    const element = document.getElementById(field);
    if (element) {
      let key = field.replace('summary', '').toLowerCase();
      key = KEY_MAP[key] || key;
      element.textContent = data[key] ?? '';
    }
  });

  updateLocationDescription();
}

function updateLocationDescription() {
  const selectElement = document.getElementById('location_description');
  const summaryElement = document.getElementById('summaryLocationDescription');
  
  if (selectElement && summaryElement) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    summaryElement.textContent = selectedOption ? selectedOption.text : '';
  }
}

function debounce(func, delay) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

document.addEventListener('DOMContentLoaded', () => {
  initSummaryMap();
  updateSummary();

  const form = document.getElementById('mainForm');
  if (form) {
    form.addEventListener('input', updateSummary);
  }

  window.addEventListener('resize', () => {
    if (summaryMap) {
      requestAnimationFrame(() => summaryMap.invalidateSize());
    }
  });
});