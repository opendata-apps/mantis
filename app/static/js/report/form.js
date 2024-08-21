function setLocalStorageWithExpiry(key, value, ttl) {
  const now = new Date();
  const item = {
    value: value,
    expiry: now.getTime() + ttl,
  };
  try {
    localStorage.setItem(key, JSON.stringify(item));
  } catch (e) {
    console.error("Error setting localStorage item:", e);
  }
}

function getLocalStorageWithExpiry(key) {
  try {
    const itemStr = localStorage.getItem(key);
    if (!itemStr) {
      return null;
    }
    const item = JSON.parse(itemStr);
    const now = new Date();
    if (now.getTime() > item.expiry) {
      localStorage.removeItem(key);
      return null;
    }
    return item.value;
  } catch (e) {
    console.error("Error getting localStorage item:", e);
    return null;
  }
}

function cleanupExpiredItems() {
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    getLocalStorageWithExpiry(key);
  }
}

function saveFormDataToLocalStorage() {
  const form = document.getElementById('mainForm');
  const formData = new FormData(form);
  const data = {};

  for (const [key, value] of formData.entries()) {
    if (key !== "csrf_token" && key !== "picture") {
      data[key] = value;
    }
  }

  setLocalStorageWithExpiry('formData', JSON.stringify(data), 3600000);
}

function loadFormDataFromLocalStorage() {
  const form = document.getElementById('mainForm');
  const storedData = getLocalStorageWithExpiry('formData');

  if (storedData) {
    try {
      const data = JSON.parse(storedData);
      for (const input of form.elements) {
        if (input.name && input.type !== 'file' && data.hasOwnProperty(input.name)) {
          input.value = data[input.name];
        }
      }
    } catch (e) {
      console.error('Error parsing stored form data:', e);
    }
  }
}

function validateForm(event, nextStepIndex) {
  event.preventDefault();
  const form = event.target.closest('form');
  const formData = new FormData();
  
  formData.append('stepIndex', nextStepIndex);
  
  for (const element of form.elements) {
    if (element.name === 'picture' && nextStepIndex !== 1) {
      continue;
    }
    if (element.type === 'file') {
      formData.append(element.name, element.files[0]);
    } else {
      formData.append(element.name, element.value);
    }
  }
  
  let csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

  const button = event.target.closest('a');
  const buttonId = button.id;
  const buttonLoader = document.getElementById(buttonId + 'Loader');
  const buttonText = document.getElementById(buttonId + 'Text');

  if (!buttonLoader || !buttonText) {
    console.error('Button loader or text not found');
    return;
  }

  if (buttonLoader.classList.contains('loading')) {
    return;
  }

  buttonLoader.classList.add('loading');
  buttonLoader.classList.remove('hidden');
  buttonText.classList.add('hidden');

  fetch('/validate', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken
    },
    body: formData
  })
    .then(response => {
      buttonLoader.classList.remove('loading');
      buttonLoader.classList.add('hidden');
      buttonText.classList.remove('hidden');

      if (!response.ok && response.status !== 333) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      const currentStepErrors = showErrors(data.errors, form.dataset.currentStep);
      if (currentStepErrors.length === 0) {
        if (nextStepIndex === 2) {
          checkAddressData(formData, nextStepIndex);
        } else {
          showStep(nextStepIndex);
        }
      }
    })
    .catch(error => {
      buttonLoader.classList.remove('loading');
      buttonLoader.classList.add('hidden');
      buttonText.classList.remove('hidden');
      console.error(error);
    });
}

function checkAddressData(formData, nextStepIndex) {
  const userState = formData.get('state');
  const userDistrict = formData.get('district');
  const userCity = formData.get('city');

  const errors = {};

  if (addressData.state && userState !== addressData.state) {
    errors.state = ['Das eingegebene Bundesland stimmt nicht mit den Fundort-Koordinaten überein.'];
  }
  if (addressData.district && userDistrict !== addressData.district) {
    errors.district = ['Der eingegebene Landkreis stimmt nicht mit den Fundort-Koordinaten überein.'];
  }
  if (addressData.city && userCity !== addressData.city) {
    errors.city = ['Der eingegebene Ort stimmt nicht mit den Fundort-Koordinaten überein.'];
  }

  if (Object.keys(errors).length > 0) {
    showErrors(errors, 1);
  } else {
    showStep(nextStepIndex);
  }
}

function showErrors(errors, currentStepIndex) {
  currentStepIndex = parseInt(currentStepIndex);

  const errorElements = document.querySelectorAll('.form-error');
  errorElements.forEach(el => {
    el.previousElementSibling.classList.remove('error-field');
    el.remove();
  });

  const pictureLabel = document.querySelector('label[for="picture"]');
  if (pictureLabel) {
    pictureLabel.classList.remove('error-field');
  }

  let currentStepErrors = [];

  for (let fieldName in errors) {
    const fieldErrors = errors[fieldName];
    const field = document.querySelector(`[name="${fieldName}"]`);
    if (field && field.closest('.step') && parseInt(field.closest('.step').dataset.stepIndex) === currentStepIndex) {
      if (fieldName === 'picture') {
        const label = document.querySelector(`label[for="${fieldName}"]`);
        label.classList.add('error-field');
      } else {
        field.classList.add('error-field');
      }

      const errorContainer = document.createElement('div');
      errorContainer.classList.add('form-error');
      errorContainer.style.display = 'flex';
      errorContainer.style.alignItems = 'center';
      errorContainer.style.margin = '0 0 0.5rem 0';
      errorContainer.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4" style="margin-right: 0.5rem;">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <span style="font-size: 0.75rem;">${fieldErrors.join(', ')}</span>
      `;

      field.parentElement.insertBefore(errorContainer, field.nextSibling);
      currentStepErrors.push(fieldName);
    }
  }

  return currentStepErrors;
}

const steps = ['step1', 'step2', 'step3', 'step4'];
const stepElements = steps.map(step => document.getElementById(step));
const [step1, step2, step3, step4] = stepElements;

const stepButtons = [
  { element: document.getElementById('step1Next'), action: (event) => validateForm(event, 1) },
  { element: document.getElementById('step2Prev'), action: () => showStep(0) },
  { element: document.getElementById('step2Next'), action: (event) => validateForm(event, 2) },
  { element: document.getElementById('step3Prev'), action: () => showStep(1) },
  { element: document.getElementById('step3Next'), action: (event) => validateForm(event, 3) },
  { element: document.getElementById('step4Prev'), action: () => showStep(2) },
];

stepButtons.forEach(({ element, action }) => {
  element.addEventListener('click', action);
});

const additionalFields = document.getElementById('additionalFields');
const form = document.getElementById('mainForm');

function showStep(index) {
  form.dataset.currentStep = index;

  stepElements.forEach((step, i) => {
    step.classList.toggle('hidden', index !== i);
  });

  if (index === 3) {
    setTimeout(() => {
      summaryMap.invalidateSize();
    }, 400);  
  }

  if (index === 2) {
    additionalFields.classList.toggle('hidden', form.identical_finder_melder.checked);
  }
}

form.identical_finder_melder.addEventListener('change', () => {
  additionalFields.classList.toggle('hidden', form.identical_finder_melder.checked);
});

function autoCompleteData(inputField, zipCode, city, district, state) {
  var inputs = ['zip_code', 'city', 'district', 'state'];

  for (const id of inputs) {
    if (inputField.id === id) continue;
    let fieldValue = null;

    switch (id) {
      case 'zip_code':
        fieldValue = zipCode;
        break;
      case 'city':
        fieldValue = city;
        break;
      case 'district':
        fieldValue = district;
        break;
      case 'state':
        fieldValue = state;
        break;
    }

    document.getElementById(id).value = fieldValue || '';
  }
}

document.getElementById('mainForm').addEventListener('submit', (event) => {
  event.preventDefault();
  var loadingMsg = document.getElementById('loadSend');
  var submitBtn = document.getElementById('submitBtn');
  var send = document.getElementById('send');

  submitBtn.disabled = true;
  send.classList.add('hidden');
  loadingMsg.classList.remove('hidden');

  try {
    localStorage.clear();
  } catch (e) {
    console.error('Error clearing localStorage:', e);
  }
  
  if (!submitBtn.classList.contains('form-submitted')) {
    submitBtn.classList.add('form-submitted');
    event.target.submit();
  }
});

document.addEventListener('DOMContentLoaded', () => {
  cleanupExpiredItems();
  loadFormDataFromLocalStorage();
  document.getElementById('mainForm').addEventListener('input', saveFormDataToLocalStorage);
});