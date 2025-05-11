const FormHelpers = {
    showLoadingOverlay: function(elements, show, message = 'Wird verarbeitet...') {
        if (!elements.loadingOverlay || !elements.loadingMessage) return;
        
        elements.loadingMessage.textContent = message;
        
        if (show) {
            elements.loadingOverlay.classList.remove('opacity-0', 'invisible');
            elements.loadingOverlay.classList.add('opacity-100');
        } else {
            elements.loadingOverlay.classList.remove('opacity-100');
            elements.loadingOverlay.classList.add('opacity-0', 'invisible');
        }
    },

    showFieldError: function(elements, fieldId, message) {
        // Special case for coordinates (map)
        if (fieldId === 'coordinates' || fieldId === 'map') {
            const mapContainer = elements.mapContainer;
            if (mapContainer) {
                let errorElement = mapContainer.parentElement.querySelector('.field-error-message');
                if (!errorElement) {
                    errorElement = document.createElement('div');
                    errorElement.className = 'field-error-message text-red-500 text-sm mt-1'; // Added error text classes
                    mapContainer.after(errorElement);
                }
                errorElement.textContent = message;
                 mapContainer.classList.add('border-red-500'); // Add border to map on error
            }
            return;
        }
        
        // Special case for photo
        if (fieldId === 'photo') {
            const container = elements.photoPreview && !elements.photoPreview.classList.contains('hidden') 
                ? elements.photoPreview 
                : elements.photoDropzone;
                
            if (container) {
                let errorElement = container.parentElement.querySelector('.field-error-message');
                if (!errorElement) {
                    errorElement = document.createElement('div');
                    errorElement.className = 'field-error-message text-red-500 text-sm mt-1'; // Added error text classes
                    container.after(errorElement);
                }
                errorElement.textContent = message;
                // Add visual indication to dropzone/preview container if needed
                container.classList.add('border-red-500'); 
            }
            return;
        }
        
        // General case - find the field and show error
        const field = document.getElementById(fieldId);
        if (!field) {
            console.warn(`Field with ID "${fieldId}" not found for error message.`);
            return;
        }
        
        // Add error styling to the field
        field.classList.add('border-red-500', 'invalid');
        field.setAttribute('aria-invalid', 'true');
        
        // Create or find error message element
        let errorElement = field.parentElement.querySelector(`.field-error-message[data-for="${fieldId}"]`);
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error-message text-red-500 text-sm mt-1'; // Added error text classes
            errorElement.dataset.for = fieldId;
            
            // Add to DOM (usually after the input)
            field.parentElement.appendChild(errorElement); 
            // field.after(errorElement); // Alternative placement
            
            // Set ARIA attributes
            const errorId = `error-${fieldId}`;
            errorElement.id = errorId;
            field.setAttribute('aria-describedby', errorId);
        }
        
        errorElement.textContent = message;
    },

    clearFieldError: function(elements, fieldId) {
        // Handle special cases
        if (fieldId === 'coordinates' || fieldId === 'map') {
            const mapContainer = elements.mapContainer;
            if (mapContainer) {
                const errorElement = mapContainer.parentElement.querySelector('.field-error-message');
                if (errorElement) errorElement.remove();
                mapContainer.classList.remove('border-red-500'); // Remove border
            }
            return;
        }
        
        if (fieldId === 'photo') {
            const container = elements.photoPreview || elements.photoDropzone;
            const errorElement = container?.parentElement.querySelector('.field-error-message');
            if (errorElement) errorElement.remove();
            container?.classList.remove('border-red-500');
             // Also clear error on the hidden input if necessary
            const photoInput = elements.photoInput;
             if(photoInput) {
                photoInput.classList.remove('border-red-500', 'invalid');
                 photoInput.removeAttribute('aria-invalid');
                 photoInput.removeAttribute('aria-describedby');
             }
            return;
        }
        
        // General case
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        // Remove error styling
        field.classList.remove('border-red-500', 'invalid');
        field.removeAttribute('aria-invalid');
        
        // Find and remove error message
        const errorElement = field.parentElement.querySelector(`.field-error-message[data-for="${fieldId}"]`);
        if (errorElement) {
            errorElement.remove();
            field.removeAttribute('aria-describedby');
        }
    },

    clearAllErrors: function(elements, stepIndex) { // Expects 0-based index
        if (!elements.steps || stepIndex < 0 || stepIndex >= elements.steps.length) return;
        
        const currentStepElement = elements.steps[stepIndex];
        
        // Remove all error messages within the current step
        const errorMessages = currentStepElement.querySelectorAll('.field-error-message');
        errorMessages.forEach(el => el.remove());
        
        // Remove error styling from inputs within the current step
        const invalidInputs = currentStepElement.querySelectorAll('.invalid, .border-red-500');
        invalidInputs.forEach(input => {
            input.classList.remove('border-red-500', 'invalid');
            input.removeAttribute('aria-invalid');
            input.removeAttribute('aria-describedby');
        });
        
        // Also clear potential map/photo errors which might visually belong to step 1/2 but whose error messages might linger
        this.clearFieldError(elements, 'coordinates');
        this.clearFieldError(elements, 'photo');
        // Clear general error near submit button
        const generalError = elements.submitBtn?.parentElement.querySelector('.field-error-message');
        if (generalError) generalError.remove();
    },

    isValidImageType: function(file) {
        const validMimeTypes = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 
            'image/heic', 'image/heif'
        ];
        const validExtensions = ['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'];
        
        const fileExtension = file.name.toLowerCase().split('.').pop();
        // Prioritize checking mime type if available, fallback to extension
        const isValidMimeType = file.type && validMimeTypes.includes(file.type.toLowerCase());
        const isValidExtension = validExtensions.includes(fileExtension);
        
        // Accept if either mime type is valid OR extension is valid (more robust)
        return isValidMimeType || isValidExtension; 
    },

    isValidImageSize: function(file) {
        return file.size <= 12 * 1024 * 1024; // 12MB
    },

    showDropzoneLoading: function(elements, isLoading, message = '') {
        if (!elements.dropzoneLoadingIndicator) return;
        
        if (isLoading) {
            elements.dropzoneLoadingIndicator.classList.remove('hidden');
            if (elements.dropzoneLoadingMessage && message) {
                elements.dropzoneLoadingMessage.textContent = message;
            }
        } else {
            elements.dropzoneLoadingIndicator.classList.add('hidden');
        }
    }
}; 