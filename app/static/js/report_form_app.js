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
        urls: {
            validateStep: '/validate-step',
            submitForm: '/report'
        },
        mapDefaults: {
            center: [51.1657, 10.4515],
            zoom: 6,
            sightingZoom: 14
        },
        maxDescLength: 500
    },

    state: {
        currentStep: 0,
        map: null,
        marker: null,
        geocoder: null,
        geocodeDebounceTimer: null,
        lastMapClick: 0,
        hasExifData: false,
        convertedWebpData: null,
        descriptionDebounceTimer: null
    },

    elements: {},

    initialize: function() {
        this.cacheElements();
        
        if (!this.elements.form || !this.elements.csrfToken) {
            console.error("Form or CSRF token not found.");
            return;
        }

        this.initializeUrls();
        this.showStep(this.state.currentStep);
        this.initializeHandlers();
        this.setupFormInteractions();
        this.setupStepNavigation(); 
        this.setupFormSubmission();   
    },

    initializeUrls: function() {
        this.config.urls.validateStep = this.elements.form.dataset.validateUrl || '/validate-step';
        this.config.urls.submitForm = this.elements.form.action;
    },

    initializeHandlers: function() {
        MapHandler.initialize(this.state, this.elements, this.config, FormHelpers);
        const mapUpdateCallback = MapHandler.updateMapWithCoordinates.bind(MapHandler);
        PhotoHandler.initialize(this.state, this.elements, this.config, FormHelpers, mapUpdateCallback);
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
                this.elements[key] = null;
            }
        }
        
        this.cacheAdditionalElements();
    },

    cacheAdditionalElements: function() {
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

    setupFormInteractions: function() {
        this.setupFinderToggle();
        this.setupCharacterCount();
    },

    setupFinderToggle: function() {
        if (this.elements.identicalFinderCheckbox && this.elements.finderFields) {
            this.elements.identicalFinderCheckbox.addEventListener('change', this.toggleFinderFields.bind(this));
            this.toggleFinderFields();
        }
    },

    setupCharacterCount: function() {
        if (this.elements.descriptionField && this.elements.charCount) {
            this.elements.descriptionField.addEventListener('input', this.updateCharCount.bind(this));
            this.updateCharCount();
        }
    },

    toggleFinderFields: function() {
        if (!this.elements.identicalFinderCheckbox || !this.elements.finderFields) return;
        
        const isChecked = this.elements.identicalFinderCheckbox.checked;
        this.elements.finderFields.style.display = isChecked ? 'none' : 'block';
        
        if (isChecked) {
            this.clearFinderFields();
        }
    },

    clearFinderFields: function() {
        const finderFirstName = document.getElementById('finder_first_name');
        const finderLastName = document.getElementById('finder_last_name');
        if (finderFirstName) finderFirstName.value = '';
        if (finderLastName) finderLastName.value = '';
    },

    updateCharCount: function() {
        if (!this.elements.descriptionField || !this.elements.charCount) return;
        
        clearTimeout(this.state.descriptionDebounceTimer);
        this.state.descriptionDebounceTimer = setTimeout(() => {
            const remaining = this.config.maxDescLength - this.elements.descriptionField.value.length;
            this.elements.charCount.textContent = remaining;
            this.elements.charCount.style.color = remaining < 0 ? '#ef4444' : '';
        }, 100);
    },

    setupStepNavigation: function() {
        this.setupNextButtons();
        this.setupPrevButtons();
        this.setupEditButtons();
    },

    setupNextButtons: function() {
        if (this.elements.nextBtns) {
            this.elements.nextBtns.forEach((btn, index) => {
                btn.addEventListener('click', () => this.validateAndGoToNextStep(index, index + 1));
            });
        }
    },

    setupPrevButtons: function() {
        if (this.elements.prevBtns) {
            this.elements.prevBtns.forEach(btn => {
                const currentStepIndex = parseInt(btn.id.replace('prev', ''), 10) - 1;
                btn.addEventListener('click', () => this.goToStep(currentStepIndex - 1));
            });
        }
    },

    setupEditButtons: function() {
        if (this.elements.editBtns) {
            this.elements.editBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const stepToEdit = parseInt(btn.dataset.step, 10);
                    if (!isNaN(stepToEdit)) {
                        this.goToStep(stepToEdit - 1);
                    }
                });
            });
        }
    },
    
    showStep: function(stepIndex) {
        if (!this.isValidStepIndex(stepIndex)) return;
        
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

    isValidStepIndex: function(stepIndex) {
        return this.elements.steps && 
               stepIndex >= 0 && 
               stepIndex < this.elements.steps.length;
    },

    goToStep: function(stepIndex) {
        if (!this.isValidStepIndex(stepIndex)) return;
        
        this.showStep(stepIndex);
        
        if (stepIndex === 1 && this.state.map) {
            this.handleLocationStepActivation();
        }
    },

    handleLocationStepActivation: function() {
        setTimeout(() => {
            this.state.map.invalidateSize();
            if (typeof MapHandler !== 'undefined' && MapHandler.autoRequestLocationIfNeeded) {
                MapHandler.autoRequestLocationIfNeeded();
            }
        }, 100);
    },

    validateAndGoToNextStep: async function(currentStepIndex, nextStepIndex) {
        if (!this.validateStepClientSide(currentStepIndex + 1)) return;

        if (currentStepIndex === 0 && !this.state.convertedWebpData) {
            FormHelpers.showFieldError(this.elements, 'photo', 'Bitte laden Sie ein Foto hoch...');
            return;
        }

        const serverIsValid = await this.performServerValidation(currentStepIndex);
        
        if (serverIsValid) {
            this.proceedToNextStep(nextStepIndex);
        }
    },

    performServerValidation: async function(currentStepIndex) {
        const needsServerValidation = currentStepIndex < 3;
        if (!needsServerValidation) return true;

        const button = document.getElementById(`next${currentStepIndex + 1}`);
        if (button) button.disabled = true;
        FormHelpers.showLoadingOverlay(this.elements, true, "Validiere Eingaben...");
        
        const isValid = await this.validateStepWithServer(currentStepIndex + 1);
        
        FormHelpers.showLoadingOverlay(this.elements, false);
        if (button) button.disabled = false;
        
        return isValid;
    },

    proceedToNextStep: function(nextStepIndex) {
        if (nextStepIndex === 3) {
            this.updateReviewContent();
        }
        this.goToStep(nextStepIndex);
        
        if (nextStepIndex === 1 && this.state.map) {
            this.handleLocationStepActivation();
        }
    },
    
    validateStepClientSide: function(stepNumber) {
        FormHelpers.clearAllErrors(this.elements, stepNumber - 1);
        
        if (stepNumber === 2) {
            return this.validateLocationStep();
        }
        
        return true;
    },

    validateLocationStep: function() {
        const lat = this.elements.latInput?.value;
        const lng = this.elements.lngInput?.value;
        
        if (!lat || !lng) {
            FormHelpers.showFieldError(this.elements, 'coordinates', 'Bitte wählen Sie einen Standort auf der Karte.');
            return false;
        }
        return true;
    },
    
    validateStepWithServer: async function(stepNumber) {
        const jsonData = this.buildValidationData(stepNumber);
        
        try {
            const response = await this.sendValidationRequest(jsonData);
            const data = await response.json();
            
            FormHelpers.clearAllErrors(this.elements, stepNumber - 1);
            
            if (!response.ok) {
                this.handleServerError(data);
                return false;
            }

            if (!data.valid) {
                if (data.errors) {
                    this.displayServerErrors(data.errors);
                }
                return false;
            }
            
            return true;

        } catch (error) {
            console.error('Server validation error:', error);
            FormHelpers.clearAllErrors(this.elements, stepNumber - 1);
            FormHelpers.showFieldError(this.elements, 'general', 'Netzwerkfehler oder Server nicht erreichbar.');
            return false;
        }
    },

    buildValidationData: function(stepNumber) {
        const formData = new FormData(this.elements.form);
        const jsonData = {};
        
        formData.forEach((value, key) => {
            if (key !== 'photo') jsonData[key] = value;
        });
        
        jsonData.step = stepNumber;
        jsonData.latitude = this.elements.latInput?.value || '';
        jsonData.longitude = this.elements.lngInput?.value || '';
        
        return jsonData;
    },

    sendValidationRequest: function(jsonData) {
        return fetch(this.config.urls.validateStep, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.elements.csrfToken
            },
            body: JSON.stringify(jsonData)
        });
    },

    handleServerError: function(data) {
        console.error('Server validation error:', data);
        if (data?.errors) {
            this.displayServerErrors(data.errors);
        } else {
            FormHelpers.showFieldError(this.elements, 'general', data.error || 'Serverfehler bei der Validierung.');
        }
    },
    
    displayServerErrors: function(errors) {
        let firstErrorField = null;
        
        for (const field in errors) {
            if (!firstErrorField) firstErrorField = field;
            const message = Array.isArray(errors[field]) ? errors[field][0] : errors[field];
            FormHelpers.showFieldError(this.elements, field, message);
        }
        
        this.scrollToFirstError(firstErrorField);
    },

    scrollToFirstError: function(fieldId) {
        if (fieldId) {
            const element = document.getElementById(fieldId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    },

    updateReviewContent: function() {
        this.updateReviewPhoto();
        this.updateReviewDetails();
        this.updateReviewLocation();
        this.updateReviewPersons();
        this.updateReviewFeedback();
    },

    updateReviewPhoto: function() {
        if (this.state.convertedWebpData?.dataUrl && this.elements.reviewPhoto) {
            this.elements.reviewPhoto.src = this.state.convertedWebpData.dataUrl;
        }
    },

    updateReviewDetails: function() {
        if (this.elements.reviewGender) {
            this.elements.reviewGender.textContent = document.getElementById('gender')?.selectedOptions[0]?.text || '-';
        }
        if (this.elements.reviewLocationDesc) {
            this.elements.reviewLocationDesc.textContent = document.getElementById('location_description')?.selectedOptions[0]?.text || '-';
        }
        if (this.elements.reviewDescription) {
            this.elements.reviewDescription.textContent = this.elements.descriptionField?.value.trim() || '-';
        }
    },

    updateReviewLocation: function() {
        if (this.elements.reviewDate) {
            const dateText = this.elements.sightingDateInput?.value 
                ? new Date(this.elements.sightingDateInput.value).toLocaleDateString('de-DE') 
                : '-';
            this.elements.reviewDate.textContent = dateText;
        }
        
        if (this.elements.reviewCoordinates) {
            const lat = this.elements.latInput?.value;
            const lng = this.elements.lngInput?.value;
            const coordText = (lat && lng) 
                ? `${parseFloat(lat).toFixed(6)}, ${parseFloat(lng).toFixed(6)}` 
                : '-';
            this.elements.reviewCoordinates.textContent = coordText;
        }
        
        this.updateAddressFields();
    },

    updateAddressFields: function() {
        const addressMappings = [
            { element: this.elements.reviewStreet, field: this.elements.addressFields.street },
            { element: this.elements.reviewZip, field: this.elements.addressFields.zipCode },
            { element: this.elements.reviewCity, field: this.elements.addressFields.city },
            { element: this.elements.reviewState, field: this.elements.addressFields.state },
            { element: this.elements.reviewDistrict, field: this.elements.addressFields.district }
        ];
        
        addressMappings.forEach(({ element, field }) => {
            if (element) {
                element.textContent = field?.value.trim() || '-';
            }
        });
    },

    updateReviewPersons: function() {
        this.updateReporterInfo();
        this.updateFinderInfo();
    },

    updateReporterInfo: function() {
        const firstName = document.getElementById('report_first_name')?.value || '';
        const lastName = document.getElementById('report_last_name')?.value || '';
        
        if (this.elements.reviewReporterName) {
            this.elements.reviewReporterName.textContent = `${firstName} ${lastName}`.trim() || '-';
        }
        if (this.elements.reviewEmail) {
            this.elements.reviewEmail.textContent = document.getElementById('email')?.value || '-';
        }
    },

    updateFinderInfo: function() {
        if (!this.elements.reviewFinderContainer || !this.elements.identicalFinderCheckbox) return;
        
        if (this.elements.identicalFinderCheckbox.checked) {
            this.elements.reviewFinderContainer.classList.add('hidden');
        } else {
            const firstName = document.getElementById('finder_first_name')?.value || '';
            const lastName = document.getElementById('finder_last_name')?.value || '';
            const finderName = `${firstName} ${lastName}`.trim();
            
            if (finderName) {
                if (this.elements.reviewFinderName) {
                    this.elements.reviewFinderName.textContent = finderName;
                }
                this.elements.reviewFinderContainer.classList.remove('hidden');
            } else {
                this.elements.reviewFinderContainer.classList.add('hidden');
            }
        }
    },

    updateReviewFeedback: function() {
        const feedbackSourceSelect = document.getElementById('feedback_source');
        const feedbackDetailInput = document.getElementById('feedback_detail');
        
        if (!this.elements.reviewFeedbackSource || !feedbackSourceSelect) return;
        
        if (feedbackSourceSelect.value) {
            const selectedText = feedbackSourceSelect.options[feedbackSourceSelect.selectedIndex].text;
            this.elements.reviewFeedbackSource.textContent = selectedText;
            
            this.updateFeedbackDetail(feedbackDetailInput);
        } else {
            this.elements.reviewFeedbackSource.textContent = 'Nicht angegeben';
            if (this.elements.reviewFeedbackDetail) {
                this.elements.reviewFeedbackDetail.classList.add('hidden');
            }
        }
    },

    updateFeedbackDetail: function(feedbackDetailInput) {
        if (this.elements.reviewFeedbackDetail && feedbackDetailInput && feedbackDetailInput.value.trim()) {
            this.elements.reviewFeedbackDetail.textContent = `Details: ${feedbackDetailInput.value.trim()}`;
            this.elements.reviewFeedbackDetail.classList.remove('hidden');
        } else if (this.elements.reviewFeedbackDetail) {
            this.elements.reviewFeedbackDetail.classList.add('hidden');
        }
    },

    setupFormSubmission: function() {
        if (!this.elements.form) return;
        this.elements.form.addEventListener('submit', this.handleFormSubmit.bind(this));
    },

    handleFormSubmit: async function(e) {
        e.preventDefault();
        
        if (!this.validateStepClientSide(this.state.currentStep + 1)) {
            console.warn('Client-side validation failed on submit.');
            return;
        }

        if (!this.state.convertedWebpData?.blob) {
            FormHelpers.showFieldError(this.elements, 'photo', 'Kein gültiges Bild zum Senden vorhanden.');
            this.goToStep(0);
            return;
        }

        this.prepareSubmission();
        
        try {
            const formData = this.buildSubmissionData();
            const response = await this.sendFormData(formData);
            await this.handleSubmissionResponse(response);
        } catch (error) {
            this.handleSubmissionError(error);
        }
    },

    prepareSubmission: function() {
        FormHelpers.showLoadingOverlay(this.elements, true, "Sende Ihre Meldung...");
        if (this.elements.submitBtn) this.elements.submitBtn.disabled = true;
    },

    buildSubmissionData: function() {
        const formData = new FormData(this.elements.form);
        formData.delete('photo');
        
        const webpFile = this.createWebpFile();
        formData.append('photo', webpFile);

        if (!formData.has('csrf_token') && this.elements.csrfToken) {
            formData.append('csrf_token', this.elements.csrfToken);
        }

        return formData;
    },

    createWebpFile: function() {
        const originalName = this.state.convertedWebpData.originalFileName || 'sighting.webp';
        const fileNameWithoutExt = originalName.substring(0, originalName.lastIndexOf('.')) || originalName;
        const webpFileName = `${fileNameWithoutExt}.webp`;
        
        return new File([this.state.convertedWebpData.blob], webpFileName, {
            type: 'image/webp',
            lastModified: Date.now()
        });
    },

    sendFormData: function(formData) {
        return fetch(this.config.urls.submitForm, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.elements.csrfToken
            }
        });
    },

    handleSubmissionResponse: async function(response) {
        if (!response.ok) {
            const errorMessage = await this.parseErrorResponse(response);
            throw new Error(errorMessage);
        }
        
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const data = await response.json().catch(() => ({}));
            window.location.href = data.redirect_url || '/success';
        }
    },

    parseErrorResponse: async function(response) {
        let errorMessage = `Serverfehler: ${response.status} ${response.statusText}`;
        
        try {
            const errorData = await response.json();
            if (errorData?.error) {
                errorMessage = `Fehler: ${errorData.error}`;
            } else if (errorData?.message) {
                errorMessage = `Fehler: ${errorData.message}`;
            }
        } catch (parseError) {
            console.warn('Could not parse error response.');
        }
        
        return errorMessage;
    },

    handleSubmissionError: function(error) {
        console.error('Form submission error:', error);
        FormHelpers.showLoadingOverlay(this.elements, false);
        if (this.elements.submitBtn) this.elements.submitBtn.disabled = false;
        
        const errorMessage = this.getErrorMessage(error);
        FormHelpers.showFieldError(this.elements, 'general', errorMessage);
        this.showSubmitButtonError(errorMessage);
    },

    getErrorMessage: function(error) {
        if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
            return 'Netzwerkfehler. Bitte Internetverbindung überprüfen.';
        } else if (error.message.includes('413') || error.message.includes('Payload Too Large')) {
            return 'Datei ist zu groß (max. 12MB).';
        }
        return error.message || 'Ein Fehler ist beim Senden aufgetreten. Bitte versuchen Sie es erneut.';
    },

    showSubmitButtonError: function(errorMessage) {
        const container = this.elements.submitBtn?.parentElement;
        if (!container || container.querySelector('.field-error-message[data-general-submit-error]')) return;
        
        const errorEl = document.createElement('div');
        errorEl.className = 'mt-2 w-full text-sm text-center text-red-500 field-error-message';
        errorEl.dataset.generalSubmitError = 'true';
        errorEl.textContent = errorMessage;
        container.appendChild(errorEl);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    ReportFormApp.initialize();
}); 