const input = document.getElementById('picture');
const preview = document.getElementById('previewImage');
const previewContainer = document.getElementById('imagePreview');
const uploadText = document.getElementById('uploadText');
const uploadLoader = document.getElementById('uploadLoader');
const dropArea = document.querySelector('label[for="picture"]');

const VALID_FILE_TYPES = ["image/png", "image/jpeg", "image/jfif", "image/webp", "image/heic", "image/heif"];
const VALID_EXTENSIONS = ["png", "jpg", "jpeg", "jfif", "webp", "heic", "heif"];
const MAX_FILE_SIZE = 12 * 1024 * 1024; // 12 MB

function init() {
  input.addEventListener('change', handleImageUpload);
  dropArea.addEventListener('dragenter', preventDefault);
  dropArea.addEventListener('dragover', preventDefault);
  dropArea.addEventListener('dragleave', unhighlightDropArea);
  dropArea.addEventListener('drop', handleDrop);
  
  document.addEventListener('DOMContentLoaded', setupExifReader);
}

function preventDefault(e) {
  e.preventDefault();
  e.stopPropagation();
  highlightDropArea();
}

function highlightDropArea() {
  dropArea.classList.add('bg-green-100', 'border-green-300');
}

function unhighlightDropArea(e) {
  preventDefault(e);
  dropArea.classList.remove('bg-green-100', 'border-green-300');
}

function handleImageUpload(e) {
  const file = e.target.files[0];
  processFile(file);
}

function handleDrop(e) {
  preventDefault(e);
  unhighlightDropArea(e);
  const file = e.dataTransfer.files[0];
  processFile(file);
}

function processFile(file) {
  clearErrorsForField('picture');

  if (!file) {
    resetPreview();
    return;
  }

  if (!isValidFile(file)) {
    showFileError();
    return;
  }

  showUploadingState();
  convertImageToWebP(file);
}

function isValidFile(file) {
  const fileType = file.type.toLowerCase();
  const fileExtension = file.name.split('.').pop().toLowerCase();
  return VALID_FILE_TYPES.includes(fileType) || VALID_EXTENSIONS.includes(fileExtension);
}

function showFileError() {
  const msg = "Erlaubt sind PNG, JPG, JPEG, HEIC, HEIF und WebP Dateien.";
  showErrors({ picture: [msg] }, 0);
  input.value = '';
}

function showUploadingState() {
  uploadText.style.display = 'none';
  uploadLoader.classList.remove('hidden');
}

function convertImageToWebP(file) {
  const isHeicOrHeif = file.type.toLowerCase().startsWith('image/heic') || 
                       file.type.toLowerCase().startsWith('image/heif') ||
                       file.name.toLowerCase().endsWith('.heic') || 
                       file.name.toLowerCase().endsWith('.heif');

  if (isHeicOrHeif) {
    convertHeicToJpeg(file);
  } else {
    convertToWebP(file, 0.7);
  }
}

function convertHeicToJpeg(file) {
  heic2any({
    blob: file,
    toType: "image/jpeg",
  }).then(resultBlob => {
    const quality = resultBlob.size > 10 * 1024 * 1024 ? 0.5 : 0.7;
    convertToWebP(resultBlob, quality);
  }).catch(error => {
    console.error(error.message);
    resetUploadState();
  });
}

function convertToWebP(file, quality) {
  const img = new Image();
  img.onload = function() {
    const canvas = document.createElement('canvas');
    canvas.width = img.width;
    canvas.height = img.height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, img.width, img.height);
    canvas.toBlob(handleConvertedBlob, 'image/webp', quality);
  };
  img.src = URL.createObjectURL(file);
}

function handleConvertedBlob(blob) {
  const convertedFile = new File([blob], 'image.webp', { type: 'image/webp' });
  
  if (convertedFile.size > MAX_FILE_SIZE) {
    alert("Das Bild ist zu groß. Bitte verwenden Sie ein kleineres Bild oder reduzieren Sie die Bildqualität.");
    resetUploadState();
    return;
  }
  
  updateInputFile(convertedFile);
  updatePreview(convertedFile);
  resetUploadState();
}

function updateInputFile(file) {
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  input.files = dataTransfer.files;
}

function updatePreview(file) {
  const reader = new FileReader();
  reader.onload = function(e) {
    previewContainer.style.display = 'flex';
    preview.src = e.target.result;
    uploadText.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

function resetUploadState() {
  uploadLoader.classList.add('hidden');
  uploadText.style.display = 'flex';
}

function resetPreview() {
  preview.src = '';
  previewContainer.style.display = 'none';
  resetUploadState();
}

function clearErrorsForField(fieldName) {
  const label = document.querySelector(`label[for="${fieldName}"]`);
  if (label) {
    label.classList.remove('error-field');
  }

  const field = document.querySelector(`[name="${fieldName}"]`);
  const errorElement = field.parentElement.querySelector('.form-error');
  if (errorElement) {
    field.classList.remove('error-field');
    errorElement.remove();
  }
}

function setupExifReader() {
  const pictureInput = document.querySelector('#picture');
  pictureInput.addEventListener('change', handleExifData);
}

function handleExifData(event) {
  const file = event.target.files[0];
  if (!file) return;

  EXIF.getData(file, function () {
    const lat = EXIF.getTag(this, 'GPSLatitude');
    const lng = EXIF.getTag(this, 'GPSLongitude');
    const latRef = EXIF.getTag(this, 'GPSLatitudeRef');
    const lngRef = EXIF.getTag(this, 'GPSLongitudeRef');

    if (lat && lng && latRef && lngRef) {
      const latitude = toDecimal(lat, latRef);
      const longitude = toDecimal(lng, lngRef);

      if (isValidCoordinate(latitude, longitude)) {
        updateCoordinates(latitude, longitude);
        updateMap(latitude, longitude);
        getAddressFromCoordinates(latitude, longitude);
      }
    }
  });
}

function toDecimal(coord, ref) {
  const [degrees, minutes, seconds] = coord;
  let decimal = degrees + minutes / 60 + seconds / (60 * 60);
  if (ref === 'S' || ref === 'W') {
    decimal = -decimal;
  }
  return decimal;
}

function isValidCoordinate(lat, lng) {
  return !isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0;
}

function updateCoordinates(lat, lng) {
  document.querySelector('#latitude').value = lat.toString();
  document.querySelector('#longitude').value = lng.toString();
}

function updateMap(lat, lng) {
  if (window.userMarker) window.userMarker.remove();
  window.userMarker = L.marker([lat, lng]).addTo(map);
  map.setView([lat, lng], 13);
}

init();