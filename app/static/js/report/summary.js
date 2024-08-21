let summaryMap;
let summaryMarker;
let summaryMarkerPopup;

function initSummaryMap() {
  summaryMap = L.map("summaryMap").setView([0, 0], 13);

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

function updateSummary() {
  const storedData = getLocalStorageWithExpiry('formData');

  if (storedData) {
    try {
      const data = JSON.parse(storedData);
      const newLatLng = new L.LatLng(data.latitude, data.longitude);
      summaryMarker.setLatLng(newLatLng);
      summaryMap.setView(newLatLng, 13);

      setTimeout(() => {
        summaryMap.invalidateSize();
      }, 400);

      const popupContent = `
        <strong>Straße:</strong> ${data.street}<br>
        <strong>Postleitzahl:</strong> ${data.zip_code}<br>
        <strong>Ort:</strong> ${data.city}<br>
        <strong>Landkreis/Stadt:</strong> ${data.district}<br>
        <strong>Bundesland:</strong> ${data.state}
      `;
      summaryMarkerPopup.setContent(popupContent);

      const pictureInput = document.getElementById('picture');
      const file = pictureInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function () {
          document.getElementById('summaryImage').src = reader.result;
        };
        reader.readAsDataURL(file);
      } else {
        document.getElementById('summaryImage').src = '#';
      }

      const selectLocationDescriptionElement = document.getElementById('location_description');
      const selectedLocationDescriptionText = selectLocationDescriptionElement.options[selectLocationDescriptionElement.selectedIndex].text;

      document.getElementById('summaryLongitude').textContent = data.longitude;
      document.getElementById('summaryLatitude').textContent = data.latitude;
      document.getElementById('summaryStreet').textContent = data.street;
      document.getElementById('summaryZipCode').textContent = data.zip_code;
      document.getElementById('summaryCity').textContent = data.city;
      document.getElementById('summaryDistrict').textContent = data.district;
      document.getElementById('summaryState').textContent = data.state;
      document.getElementById('summaryGender').textContent = data.gender;
      document.getElementById('summaryLocationDescription').textContent = selectedLocationDescriptionText;
      document.getElementById('summaryPictureDescription').textContent = data.picture_description;
      document.getElementById('summaryFirstName').textContent = data.report_first_name;
      document.getElementById('summaryLastName').textContent = data.report_last_name;
      document.getElementById('summarySightingDate').textContent = data.sighting_date;
      document.getElementById('summaryContact').textContent = data.contact;
    } catch (e) {
      console.error('Error parsing stored form data in updateSummary:', e);
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initSummaryMap();
  updateSummary();

  document.querySelectorAll('input, select, textarea').forEach(function (input) {
    input.addEventListener('input', updateSummary);
  });
});