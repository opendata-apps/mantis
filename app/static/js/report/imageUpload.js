const input = document.getElementById('picture');
const preview = document.getElementById('previewImage');
const previewContainer = document.getElementById('imagePreview');
const uploadText = document.getElementById('uploadText');
const uploadLoader = document.getElementById('uploadLoader');

input.addEventListener('change', handleImageUpload);
document.addEventListener('drop', dropHandler);

function handleImageUpload(e) {
  const file = e.target.files[0];
  const validFileTypes = ["image/png", "image/jpeg", "image/jfif", "image/webp", "image/heic", "image/heif"];

  clearErrorsForField('picture');

  if (file) {
    if (!validFileTypes.includes(file.type.toLowerCase())) {
      const msg = "Erlaubt sind PNG, JPG, JPEG, HEIC, HEIF und WebP Dateien.";
      showErrors({ picture: [msg] }, 0);
      e.target.value = '';
      return;
    }

    uploadText.style.display = 'none';
    uploadLoader.classList.remove('hidden');

    convertImageToWebP(file);
  } else {
    resetPreview();
  }
}

function dropHandler(ev) {
  ev.preventDefault();
  if (ev.dataTransfer.items) {
    for (var i = 0; i < ev.dataTransfer.items.length; i++) {
      if (ev.dataTransfer.items[i].kind === 'file') {
        var file = ev.dataTransfer.items[i].getAsFile();
        convertImageToWebP(file);
      }
    }
  }
}

function convertImageToWebP(file) {
  if (file.type.startsWith('image/heic') || file.type.startsWith('image/heif')) {
    heic2any({
      blob: file,
      toType: "image/jpeg",
    }).then(function (resultBlob) {
      if (resultBlob.size > 10 * 1024 * 1024) {
        convertToWebP(resultBlob, 0.5);
      } else {
        convertToWebP(resultBlob, 0.7);
      }
    }).catch(function (x) {
      console.error(x.message);
      uploadLoader.classList.add('hidden');
      uploadText.style.display = 'flex';
    });
  } else {
    convertToWebP(file, 0.7);
  }
}

function convertToWebP(file, quality) {
  var img = new Image();
  img.onload = function() {
    var canvas = document.createElement('canvas');
    canvas.width = img.width;
    canvas.height = img.height;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, img.width, img.height);
    canvas.toBlob(function(blob) {
      var convertedFile = new File([blob], 'image.webp', { type: 'image/webp' });
      
      if (convertedFile.size > 12 * 1024 * 1024) {
        alert("Das Bild ist zu groß. Bitte verwenden Sie ein kleineres Bild oder reduzieren Sie die Bildqualität.");
        uploadLoader.classList.add('hidden');
        uploadText.style.display = 'flex';
        return;
      }
      
      var dataTransfer = new DataTransfer();
      dataTransfer.items.add(convertedFile);
      input.files = dataTransfer.files;
      updatePreview(convertedFile);
      
      uploadLoader.classList.add('hidden');
    }, 'image/webp', quality);
  };
  img.src = URL.createObjectURL(file);
}

function updatePreview(file) {
  var reader = new FileReader();
  reader.onload = function(e) {
    previewContainer.style.display = 'flex';
    preview.src = e.target.result;
    uploadText.style.display = 'none';
    uploadLoader.classList.add('hidden');
  };
  reader.readAsDataURL(file);
}

function resetPreview() {
  preview.src = '';
  previewContainer.style.display = 'none';
  uploadText.style.display = 'flex';
  uploadLoader.classList.add('hidden');
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

document.addEventListener('DOMContentLoaded', function () {
  const pictureInput = document.querySelector('#picture');

  pictureInput.addEventListener('change', function (event) {
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

        if (isNaN(latitude) || isNaN(longitude) || latitude === 0 || longitude === 0) {
          return;
        }
        document.querySelector('#latitude').value = latitude.toString();
        document.querySelector('#longitude').value = longitude.toString();

        if (window.userMarker) window.userMarker.remove();
        window.userMarker = L.marker([latitude, longitude]).addTo(map);
        map.setView([latitude, longitude], 13); 

        getAddressFromCoordinates(latitude, longitude);
      }
    });
  });
});

function toDecimal(coord, ref) {
  const [degrees, minutes, seconds] = coord;
  let decimal = degrees + minutes / 60 + seconds / (60 * 60);

  if (ref === 'S' || ref === 'W') {
    decimal = -decimal;
  }

  return decimal;
}