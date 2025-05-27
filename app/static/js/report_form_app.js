// Main application logic for the report form
const ReportFormApp = {
    config: {
        selectors: {
            form: '#reportForm',
            steps: '.step',
            loadingOverlay: '#loadingOverlay',
            loadingMessage: '#loadingMessage',
            photoInput: '#photo',
            photoDropzone: '#photo-upload-area',
            photoPreview: '#photoPreview',
            previewImg: '#preview-img',
            removePhotoBtn: '#remove-photo',
            exifDataDiv: '#exif-data',
            exifDate: '#exif-date',
            exifLocation: '#exif-location',
            dropzoneLoadingIndicator: '#dropzoneLoadingIndicator',
            dropzoneLoadingMessage: '#dropzoneLoadingMessage',
            mapContainer: '#map',
            latInput: '#latitude',
            lngInput: '#longitude',
            manualLatInput: '#manual-latitude',
            manualLngInput: '#manual-longitude',
            sightingDateInput: '#sighting_date',
            identicalFinderCheckbox: '#identical_finder_reporter',
            finderFields: '#finder_fields',
            descriptionField: '#description',
            charCount: '#char-count',
            reviewPhoto: '#review-photo',
            reviewDate: '#review-date',
            reviewCoordinates: '#review-coordinates',
            reviewCity: '#review-city',
            reviewState: '#review-state',
            reviewStreet: '#review-street',
            reviewZip: '#review-zip',
            reviewDistrict: '#review-district',
            reviewLocationDesc: '#review-location-desc',
            reviewGender: '#review-gender',
            reviewDescription: '#review-description',
            reviewReporterName: '#review-reporter-name',
            reviewEmail: '#review-email',
            reviewFinderContainer: '#review-finder-container',
            reviewFinderName: '#review-finder-name',
            reviewFeedbackSource: '#review-feedback-source',
            reviewFeedbackDetail: '#review-feedback-detail',
            nextBtns: '[id^="next"]',
            prevBtns: '[id^="prev"]',
            editBtns: '.edit-btn'
        },
        urls: { // URLs should be passed from template or defined globally
            validateStep: '/validate-step', // Placeholder - fetch from data attribute or global var
            submitForm: '/report'       // Placeholder - use form action attribute
        },
        mapDefaults: {
            center: [51.1657, 10.4515], // Germany
            zoom: 6,
            sightingZoom: 14
        },
        maxDescLength: 500
    },

    state: {
        currentStep: 0,
        map: null, // Managed by MapHandler
        marker: null, // Managed by MapHandler
        geocoder: null, // Managed by MapHandler
        geocodeDebounceTimer: null,
        lastMapClick: 0,
        hasExifData: false,
        convertedWebpData: null, // { dataUrl: '', blob: null, originalFileName: '' }
        descriptionDebounceTimer: null
    },

    elements: {},

    // --- Initialization ---
    initialize: function() {
        // Check for dependencies
        if (typeof FormHelpers === 'undefined' || typeof PhotoHandler === 'undefined' || typeof MapHandler === 'undefined') {
            console.error('Missing required script dependencies (FormHelpers, PhotoHandler, MapHandler).');
            alert('Ein Fehler beim Laden der Seite ist aufgetreten. Bitte versuchen Sie es später erneut.');
            return;
        }
        
        this.cacheElements();
        
        if (!this.elements.form || !this.elements.csrfToken) {
            console.error("Form or CSRF token not found. Aborting initialization.");
            // Optionally display a user-friendly error message
            return;
        }

        // Get URLs from data attributes if available, otherwise use form action for submit
        this.config.urls.validateStep = this.elements.form.dataset.validateUrl || '/validate-step'; 
        this.config.urls.submitForm = this.elements.form.action;

        this.showStep(this.state.currentStep); // Show initial step
        
        // Initialize Handlers, passing 'this' app object for context/state sharing if needed
        // Or just pass the specific parts they need (state, elements, config, helpers)
        MapHandler.initialize(this.state, this.elements, this.config, FormHelpers); 
        // Get the map update function AFTER map handler is initialized
        const mapUpdateCallback = MapHandler.updateMapWithCoordinates.bind(MapHandler);
        PhotoHandler.initialize(this.state, this.elements, this.config, FormHelpers, mapUpdateCallback);
        
        // Initialize form interactions
        this.setupFormInteractions();
        this.setupStepNavigation(); 
        this.setupFormSubmission();   
    },
    
    cacheElements: function() {
        for (const key in this.config.selectors) {
            const selector = this.config.selectors[key];
            const elementList = document.querySelectorAll(selector);
            
            if (elementList.length === 1) {
                this.elements[key] = elementList[0];
            } else if (elementList.length > 1) {
                this.elements[key] = Array.from(elementList);
            } else {
                this.elements[key] = null; // Keep track even if not found
                // console.warn(`Element not found for selector: ${key} ('${selector}')`);
            }
        }
        
        // Add additional common elements
        this.elements.csrfToken = document.querySelector('input[name="csrf_token"]')?.value;
        this.elements.submitBtn = document.querySelector('button[type="submit"]');
        this.elements.addressFields = {
            zipCode: document.getElementById('fund_zip_code'),
            city: document.getElementById('fund_city'),
            state: document.getElementById('fund_state'),
            district: document.getElementById('fund_district'),
            street: document.getElementById('fund_street')
        };
    },

    // --- Form Interactions Module ---
    setupFormInteractions: function() {
        if (this.elements.identicalFinderCheckbox && this.elements.finderFields) {
            this.elements.identicalFinderCheckbox.addEventListener('change', this.toggleFinderFields.bind(this));
            this.toggleFinderFields(); // Initial state
        }
        
        if (this.elements.descriptionField && this.elements.charCount) {
            this.elements.descriptionField.addEventListener('input', this.updateCharCount.bind(this));
            this.updateCharCount(); // Initial count
        }
    },

    toggleFinderFields: function() {
        if (!this.elements.identicalFinderCheckbox || !this.elements.finderFields) return;
        
        const isChecked = this.elements.identicalFinderCheckbox.checked;
        this.elements.finderFields.style.display = isChecked ? 'none' : 'block';
        
        // Clear/disable finder fields when hidden for validation purposes
        const finderFirstName = document.getElementById('finder_first_name');
        const finderLastName = document.getElementById('finder_last_name');
        if (isChecked) {
            if(finderFirstName) finderFirstName.value = '';
            if(finderLastName) finderLastName.value = '';
            // Optionally disable them too if backend validation requires it
             // if(finderFirstName) finderFirstName.disabled = true;
             // if(finderLastName) finderLastName.disabled = true;
        } else {
             // if(finderFirstName) finderFirstName.disabled = false;
             // if(finderLastName) finderLastName.disabled = false;
        }
    },

    updateCharCount: function() {
        if (!this.elements.descriptionField || !this.elements.charCount) return;
        
        clearTimeout(this.state.descriptionDebounceTimer);
        this.state.descriptionDebounceTimer = setTimeout(() => {
            const remaining = this.config.maxDescLength - this.elements.descriptionField.value.length;
            this.elements.charCount.textContent = remaining;
            this.elements.charCount.style.color = remaining < 0 ? '#ef4444' : ''; // Use Tailwind red
        }, 100);
    },

    // --- Form Navigation and Validation Module ---
    setupStepNavigation: function() {
        if (this.elements.nextBtns) {
            this.elements.nextBtns.forEach((btn, index) => {
                btn.addEventListener('click', () => this.validateAndGoToNextStep(index, index + 1));
            });
        }
        
        if (this.elements.prevBtns) {
            this.elements.prevBtns.forEach((btn, index) => {
                // Find corresponding step index (prevBtn id is like prev2, prev3, prev4)
                const currentStepIndex = parseInt(btn.id.replace('prev', ''), 10) - 1;
                btn.addEventListener('click', () => this.goToStep(currentStepIndex - 1)); 
            });
        }
        
        if (this.elements.editBtns) {
            this.elements.editBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const stepToEdit = parseInt(btn.dataset.step, 10);
                    if (!isNaN(stepToEdit)) {
                        this.goToStep(stepToEdit - 1); // Adjust to 0-based index
                    }
                });
            });
        }
    },
    
    showStep: function(stepIndex) {
        if (!this.elements.steps || stepIndex < 0 || stepIndex >= this.elements.steps.length) return;
        
        this.elements.steps.forEach((step, index) => {
            if (index === stepIndex) {
                step.classList.remove('hidden');
                step.classList.add('active');
            } else {
                step.classList.remove('active');
                step.classList.add('hidden');
            }
        });
        this.state.currentStep = stepIndex;
    },

    goToStep: function(stepIndex) {
        if (!this.elements.steps || stepIndex < 0 || stepIndex >= this.elements.steps.length) return;
        
        this.showStep(stepIndex);
    },

    validateAndGoToNextStep: async function(currentStepIndex, nextStepIndex) {
        // Client-side validation first (pass 1-based step number)
        if (!this.validateStepClientSide(currentStepIndex + 1)) return; 

        if (currentStepIndex === 0 && !this.state.convertedWebpData) {
             FormHelpers.showFieldError(this.elements, 'photo', 'Bitte laden Sie ein Foto hoch...');
             return;
        }

        const needsServerValidation = currentStepIndex < 3; // Steps 1, 2, 3 (0-indexed) need validation
        let serverIsValid = true;

        if (needsServerValidation) {
            const button = document.getElementById(`next${currentStepIndex + 1}`);
            if (button) button.disabled = true;
            FormHelpers.showLoadingOverlay(this.elements, true, "Validiere Eingaben...");
            
            serverIsValid = await this.validateStepWithServer(currentStepIndex + 1); // Pass 1-based step index
            
            FormHelpers.showLoadingOverlay(this.elements, false);
            if (button) button.disabled = false;
        }
        
        if (serverIsValid) {
            if (nextStepIndex === 3) { // Moving to Review Step (index 3)
                this.updateReviewContent();
            }
            this.goToStep(nextStepIndex);
            
            // Re-validate map size if moving to step 2 (index 1)
            if (nextStepIndex === 1 && this.state.map) {
                setTimeout(() => {
                    this.state.map.invalidateSize();
                }, 100);
            }
        }
    },
    
    validateStepClientSide: function(stepNumber) { // Expects 1-based step number
        FormHelpers.clearAllErrors(this.elements, stepNumber - 1); // Use 0-based index for errors
        let isValid = true;

        if (stepNumber === 2) { // Location step
            const lat = this.elements.latInput?.value;
            const lng = this.elements.lngInput?.value;
            if (!lat || !lng) {
                FormHelpers.showFieldError(this.elements, 'coordinates', 'Bitte wählen Sie einen Standort auf der Karte.');
                isValid = false;
            }
        }
        // Add more client-side checks if needed (e.g., basic format checks for text fields)
        return isValid;
    },
    
    validateStepWithServer: async function(stepNumber) { // Expects 1-based step number
        const formData = new FormData(this.elements.form);
        const jsonData = {};
        formData.forEach((value, key) => {
            if (key !== 'photo') jsonData[key] = value; // Exclude file input from JSON data
        });
        jsonData.step = stepNumber;
        jsonData.latitude = this.elements.latInput?.value || ''; // Ensure coordinates are included
        jsonData.longitude = this.elements.lngInput?.value || '';
        
        try {
            const response = await fetch(this.config.urls.validateStep, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.elements.csrfToken
                },
                body: JSON.stringify(jsonData)
            });
            
            const data = await response.json(); // Assume server always returns JSON
            
            FormHelpers.clearAllErrors(this.elements, stepNumber - 1); // Clear errors for current step
            
            if (!response.ok) {
                 // Handle server-side errors (e.g., 500) or validation errors (e.g., 400/422)
                 console.error('Server validation error:', data);
                 if (data && data.errors) {
                     this.displayServerErrors(data.errors); // Display field-specific errors
                 } else {
                     FormHelpers.showFieldError(this.elements, 'general', data.error || 'Serverfehler bei der Validierung.');
                 }
                 return false;
             }

            // Check the specific success flag from the response
            if (!data.valid) {
                if (data.errors) {
                   this.displayServerErrors(data.errors);
                }
                return false;
            }
            
            return true; // Validation successful

        } catch (error) {
            console.error('Error fetching server validation:', error);
            FormHelpers.clearAllErrors(this.elements, stepNumber - 1); // Clear errors for current step
            FormHelpers.showFieldError(this.elements, 'general', 'Netzwerkfehler oder Server nicht erreichbar.');
            return false;
        }
    },
    
    displayServerErrors: function(errors) {
        let firstErrorField = null;
        for (const field in errors) {
            if (!firstErrorField) firstErrorField = field; // Track the first field with an error
            const message = Array.isArray(errors[field]) ? errors[field][0] : errors[field]; // Handle potential array/string error message
            
             // Map potential backend field names to frontend IDs if needed
             const fieldId = field; // Assuming backend names match frontend IDs for now
            
            FormHelpers.showFieldError(this.elements, fieldId, message);
        }
         // Optionally, scroll the first error field into view
         const firstErrorElement = document.getElementById(firstErrorField);
         if (firstErrorElement) {
             firstErrorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
         }
    },

    // --- Review Content Module ---
    updateReviewContent: function() {
        // Photo
        if (this.state.convertedWebpData?.dataUrl && this.elements.reviewPhoto) {
             this.elements.reviewPhoto.src = this.state.convertedWebpData.dataUrl;
        }
        
        // Details
        if (this.elements.reviewGender) this.elements.reviewGender.textContent = document.getElementById('gender')?.selectedOptions[0]?.text || '-';
        if (this.elements.reviewLocationDesc) this.elements.reviewLocationDesc.textContent = document.getElementById('location_description')?.selectedOptions[0]?.text || '-';
        if (this.elements.reviewDescription) this.elements.reviewDescription.textContent = this.elements.descriptionField?.value.trim() || '-';

        // Date & Location
        if (this.elements.reviewDate) this.elements.reviewDate.textContent = this.elements.sightingDateInput?.value ? new Date(this.elements.sightingDateInput.value).toLocaleDateString('de-DE') : '-';
        if (this.elements.reviewCoordinates) this.elements.reviewCoordinates.textContent = (this.elements.latInput?.value && this.elements.lngInput?.value) ? `${parseFloat(this.elements.latInput.value).toFixed(6)}, ${parseFloat(this.elements.lngInput.value).toFixed(6)}` : '-';
        if (this.elements.reviewStreet) this.elements.reviewStreet.textContent = this.elements.addressFields.street?.value.trim() || '-';
        if (this.elements.reviewZip) this.elements.reviewZip.textContent = this.elements.addressFields.zipCode?.value.trim() || '-';
        if (this.elements.reviewCity) this.elements.reviewCity.textContent = this.elements.addressFields.city?.value.trim() || '-';
        if (this.elements.reviewState) this.elements.reviewState.textContent = this.elements.addressFields.state?.value.trim() || '-';
        if (this.elements.reviewDistrict) this.elements.reviewDistrict.textContent = this.elements.addressFields.district?.value.trim() || '-';

        // Reporter & Finder
        const reporterFirstName = document.getElementById('report_first_name')?.value || '';
        const reporterLastName = document.getElementById('report_last_name')?.value || '';
        if (this.elements.reviewReporterName) this.elements.reviewReporterName.textContent = `${reporterFirstName} ${reporterLastName}`.trim() || '-';
        if (this.elements.reviewEmail) this.elements.reviewEmail.textContent = document.getElementById('email')?.value || '-';
        
        if (this.elements.reviewFinderContainer && this.elements.identicalFinderCheckbox) {
            if (this.elements.identicalFinderCheckbox.checked) {
                this.elements.reviewFinderContainer.classList.add('hidden');
            } else {
                const finderFirstName = document.getElementById('finder_first_name')?.value || '';
                const finderLastName = document.getElementById('finder_last_name')?.value || '';
                const finderName = `${finderFirstName} ${finderLastName}`.trim();
                if (finderName) {
                    if (this.elements.reviewFinderName) this.elements.reviewFinderName.textContent = finderName;
                    this.elements.reviewFinderContainer.classList.remove('hidden');
                } else {
                    // Hide if finder names are empty even if box is unchecked
                    this.elements.reviewFinderContainer.classList.add('hidden'); 
                }
            }
        }
        
        // Feedback Information - only process if elements exist (user hasn't provided feedback before)
        const feedbackSourceSelect = document.getElementById('feedback_source');
        const feedbackDetailInput = document.getElementById('feedback_detail');
        
        if (this.elements.reviewFeedbackSource && feedbackSourceSelect) {
            if (feedbackSourceSelect.value) {
                const selectedText = feedbackSourceSelect.options[feedbackSourceSelect.selectedIndex].text;
                this.elements.reviewFeedbackSource.textContent = selectedText;
                
                // Show detail if provided
                if (this.elements.reviewFeedbackDetail && feedbackDetailInput && feedbackDetailInput.value.trim()) {
                    this.elements.reviewFeedbackDetail.textContent = `Details: ${feedbackDetailInput.value.trim()}`;
                    this.elements.reviewFeedbackDetail.classList.remove('hidden');
                } else if (this.elements.reviewFeedbackDetail) {
                    this.elements.reviewFeedbackDetail.classList.add('hidden');
                }
            } else {
                this.elements.reviewFeedbackSource.textContent = 'Nicht angegeben';
                if (this.elements.reviewFeedbackDetail) {
                    this.elements.reviewFeedbackDetail.classList.add('hidden');
                }
            }
        }
    },

    // --- Form Submission Module ---
    setupFormSubmission: function() {
        if (!this.elements.form) return;
        this.elements.form.addEventListener('submit', this.handleFormSubmit.bind(this));
    },

    handleFormSubmit: async function(e) {
        e.preventDefault();
        
        // Final client validation (current step is review step, index 3)
        if (!this.validateStepClientSide(this.state.currentStep + 1)) { 
             console.warn('Client-side validation failed on submit.');
             // Error messages should already be shown by validateStepClientSide
             return;
        } 

        if (!this.state.convertedWebpData?.blob) {
            FormHelpers.showFieldError(this.elements, 'photo', 'Kein gültiges Bild zum Senden vorhanden.');
            this.goToStep(0); // Go back to photo step
            return;
        }

        FormHelpers.showLoadingOverlay(this.elements, true, "Sende Ihre Meldung...");
        if (this.elements.submitBtn) this.elements.submitBtn.disabled = true;

        const formData = new FormData(this.elements.form);
        // Remove original file if it exists, append the processed WebP blobbest practice big multi step form
        formData.delete('photo');
        const originalName = this.state.convertedWebpData.originalFileName || 'sighting.webp';
        const fileNameWithoutExt = originalName.substring(0, originalName.lastIndexOf('.')) || originalName;
        const webpFileName = `${fileNameWithoutExt}.webp`;
        const webpFile = new File([this.state.convertedWebpData.blob], webpFileName, { type: 'image/webp', lastModified: Date.now() });
        formData.append('photo', webpFile);

        // Include CSRF token if not already part of FormData (depends on WTForms config)
        if (!formData.has('csrf_token') && this.elements.csrfToken) {
             formData.append('csrf_token', this.elements.csrfToken);
        }

        try {
            const response = await fetch(this.config.urls.submitForm, {
                 method: 'POST',
                 body: formData,
                 // No 'Content-Type' header for FormData, browser sets it with boundary
                 headers: {
                     'X-CSRFToken': this.elements.csrfToken // Send CSRF via header too if needed by backend
                 }
            });
            
            if (!response.ok) {
                let serverErrorMsg = `Serverfehler: ${response.status} ${response.statusText}`;
                try {
                    // Attempt to parse JSON error response from server
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                       serverErrorMsg = `Fehler: ${errorData.error}`;
                    } else if (errorData && errorData.message) {
                         serverErrorMsg = `Fehler: ${errorData.message}`;
                    }
                    // TODO: Handle field-specific errors returned on final submit if necessary
                    // if (errorData && errorData.errors) { ... display errors ... }
                } catch (parseError) { 
                    console.warn('Could not parse JSON error response from server.');
                    // Optionally read response text for non-JSON errors
                     // const textError = await response.text(); 
                     // serverErrorMsg = textError || serverErrorMsg;
                }
                throw new Error(serverErrorMsg);
            }
            
            // Handle successful submission (redirect or message)
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                 // Check if response contains a success URL
                 const data = await response.json().catch(() => ({})); // Attempt to parse JSON response
                 if (data.redirect_url) {
                     window.location.href = data.redirect_url;
                 } else {
                    // Fallback redirect if no specific URL provided
                     window.location.href = '/thank-you'; // Make sure this URL exists
                 }
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            FormHelpers.showLoadingOverlay(this.elements, false);
            if (this.elements.submitBtn) this.elements.submitBtn.disabled = false;
            
            let errorMessage = 'Ein Fehler ist beim Senden aufgetreten. Bitte versuchen Sie es erneut.';
            if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                errorMessage = 'Netzwerkfehler. Bitte Internetverbindung überprüfen.';
            } else if (error.message.includes('413') || error.message.includes('Payload Too Large')) {
                errorMessage = 'Datei ist zu groß (max. 12MB).';
            } else {
                 // Use the specific error message from the catch block
                 errorMessage = error.message;
            }
             FormHelpers.showFieldError(this.elements, 'general', errorMessage); 
             // Display error near submit button as well for visibility
             const submitButtonContainer = this.elements.submitBtn?.parentElement;
             if (submitButtonContainer && !submitButtonContainer.querySelector('.field-error-message[data-general-submit-error]')) {
                  const errorEl = document.createElement('div');
                  errorEl.className = 'w-full mt-2 text-sm text-center text-red-500 field-error-message';
                  errorEl.dataset.generalSubmitError = 'true'; // Add attribute to prevent duplicates
                  errorEl.textContent = errorMessage;
                  submitButtonContainer.appendChild(errorEl);
             }
        }
    }
};

// Initialize the app once the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ReportFormApp.initialize();
}); 