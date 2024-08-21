let map;
let userMarker;

function initMap() {
  const germanyBounds = [
    [47.270111, 5.866342],
    [55.058347, 15.041896]
  ];

  map = L.map('map', {
    maxBounds: germanyBounds,
    maxBoundsViscosity: 1.0
  }).setView([52.5200, 13.4050], 7);

  const openStreetMapLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
  });

  const arcGISLayer = L.esri.Vector.vectorBasemapLayer("ArcGIS:Imagery", {
    apikey: mapApiKey
  });

  map.addLayer(openStreetMapLayer);

  const baseMaps = {
    "Karte": openStreetMapLayer,
    "Satellit": arcGISLayer
  };

  L.control.layers(baseMaps).addTo(map);
  L.control.locate(baseMaps).addTo(map);

  const MIN_ZOOM_LEVEL = 5;
  map.on('zoomend', function() {
    if (map.getZoom() < MIN_ZOOM_LEVEL) {
      map.setZoom(MIN_ZOOM_LEVEL);
    }
  });

  map.on('click', function (e) {
    updateMapAndFormData(e.latlng.lat, e.latlng.lng);
  });

  document.querySelector('#latitude').addEventListener('change', function () {
    const lat = parseFloat(this.value);
    const lng = parseFloat(document.querySelector('#longitude').value);
    if (!isNaN(lat) && !isNaN(lng)) {
      updateMapAndFormData(lat, lng);
    }
  });

  document.querySelector('#longitude').addEventListener('change', function () {
    const lng = parseFloat(this.value);
    const lat = parseFloat(document.querySelector('#latitude').value);
    if (!isNaN(lat) && !isNaN(lng)) {
      updateMapAndFormData(lat, lng);
    }
  });
}

function updateMapAndFormData(lat, lng) {
  document.querySelector('#latitude').value = lat.toString();
  document.querySelector('#longitude').value = lng.toString();

  getAddressFromCoordinates(lat, lng);

  if (userMarker) {
    userMarker.remove();
  }

  userMarker = L.marker([lat, lng]).addTo(map);

  saveFormDataToLocalStorage();
  updateSummary();

  localStorage.setItem('latitude', lat.toString());
  localStorage.setItem('longitude', lng.toString());
}

function getAddressFromCoordinates(latitude, longitude) {
  const nominatimUrl = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`;

  fetch(nominatimUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      const address = data.address;

      document.querySelector("#zip_code").value = address.postcode ? address.postcode.split(";")[0] : "";
      document.querySelector("#city").value = address.city || address.town || address.village || "";
      document.querySelector("#street").value = `${address.road || ""} ${address.house_number || ""}`.trim();
      document.querySelector("#state").value = address.state || address.city || "";
      document.querySelector("#district").value = address.county || address.suburb || address.borough || "";

      const addressData = {
        state: address.state || address.city || "",
        district: address.county || address.suburb || address.borough || "",
        city: address.city || address.town || address.village || ""
      };

      window.addressData = addressData;
    })
    .catch(error => {
      console.error("Error fetching address data:", error);
    });
}

document.addEventListener('DOMContentLoaded', initMap);