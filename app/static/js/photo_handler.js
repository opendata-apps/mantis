const PhotoHandler = {
    initialize: function(state, elements, config, helpers, mapUpdateCallback) {
        this.state = state;
        this.elements = elements;
        this.config = config;
        this.helpers = helpers;
        this.mapUpdateCallback = mapUpdateCallback;
        this.setupEventListeners();
    },

    setupEventListeners: function() {
        if (!this.elements.photoInput || !this.elements.photoDropzone) return;
        
        // Use .bind(this) to ensure 'this' refers to PhotoHandler inside handlers
        this.elements.photoInput.addEventListener('change', this.handlePhotoChange.bind(this));
        this.elements.photoDropzone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.elements.photoDropzone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.elements.photoDropzone.addEventListener('drop', this.handleDrop.bind(this));
        this.elements.photoDropzone.addEventListener('click', () => this.elements.photoInput.click());
        
        if (this.elements.removePhotoBtn) {
            this.elements.removePhotoBtn.addEventListener('click', this.removePhoto.bind(this));
        }
    },

    handleDragOver: function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('dragover'); // Use currentTarget
    },

    handleDragLeave: function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover'); // Use currentTarget
    },

    handleDrop: function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover'); // Use currentTarget
        
        if (e.dataTransfer.files.length) {
            this.elements.photoInput.files = e.dataTransfer.files;
            // Create and dispatch a 'change' event on the file input
            // so handlePhotoChange is triggered consistently.
            const changeEvent = new Event('change', { bubbles: true });
            this.elements.photoInput.dispatchEvent(changeEvent);
        }
    },

    handlePhotoChange: async function(event) { // Use event object
        const inputElement = event.target;
        if (!inputElement.files || !inputElement.files[0]) return;
        
        const file = inputElement.files[0];
        
        // Validate file type and size using helpers
        if (!this.helpers.isValidImageType(file)) {
            this.helpers.showFieldError(this.elements, 'photo', 'Bitte wählen Sie eine Bilddatei (JPG, PNG, WEBP, HEIC oder HEIF).');
            return;
        }
        
        if (!this.helpers.isValidImageSize(file)) {
            this.helpers.showFieldError(this.elements, 'photo', 'Das Bild muss kleiner als 12MB sein.');
            return;
        }
        
        // Show loading indicator using helpers
        this.helpers.showDropzoneLoading(this.elements, true, "Verarbeite Bild...");
        this.helpers.clearFieldError(this.elements, 'photo');
        
        try {
            // Process EXIF data (assumes ExifProcessor is global)
            const exifResult = await ExifProcessor.processImageExif(file)
                .catch(err => {
                    console.error("EXIF Error:", err);
                    return { error: err.message }; // Gracefully handle EXIF errors
                });

            // Convert to WebP (assumes WebpConverter is global)
            const webpResult = await WebpConverter.processImage(file)
                 .catch(err => {
                     throw new Error(`Bildkonvertierung fehlgeschlagen: ${err.message}`);
                 });

            // Store WebP data in main state
            this.state.convertedWebpData = {
                dataUrl: webpResult.dataUrl,
                blob: webpResult.blob,
                originalFileName: webpResult.originalFileName || file.name
            };
            
            // Display preview
            this.displayPhotoPreview(webpResult.dataUrl);
            
            // Apply EXIF data if available
            this.applyExifData(exifResult);
            
        } catch (error) {
            console.error('Error processing image:', error);
            
            let errorMessage = 'Ein Fehler ist beim Verarbeiten des Bildes aufgetreten.';
            if (error.message.includes('HEIC')) {
                errorMessage = 'HEIC/HEIF Bilder konnten nicht verarbeitet werden. Bitte konvertieren Sie das Bild zu JPEG oder PNG vor dem Hochladen.';
            } else if (error.message.includes('load image')) {
                errorMessage = 'Das Bild konnte nicht geladen werden. Bitte versuchen Sie ein anderes Bild.';
            } else if (error.message.includes('Bildkonvertierung')) {
                errorMessage = error.message; // Use the specific conversion error
            }
            
            this.helpers.showFieldError(this.elements, 'photo', errorMessage);
            this.removePhoto(); // Clean up UI on error
        } finally {
            this.helpers.showDropzoneLoading(this.elements, false);
        }
    },

    displayPhotoPreview: function(dataUrl) {
        if (!this.elements.photoPreview || !this.elements.previewImg) return;
        
        this.elements.photoDropzone.classList.add('hidden');
        this.elements.photoPreview.classList.remove('hidden');
        this.elements.previewImg.src = dataUrl;
    },

    removePhoto: function() {
        if (!this.elements.photoInput) return;
        
        this.elements.photoInput.value = ''; // Clear the file input
        
        if (this.elements.photoPreview) this.elements.photoPreview.classList.add('hidden');
        if (this.elements.exifDataDiv) this.elements.exifDataDiv.classList.add('hidden');
        if (this.elements.photoDropzone) this.elements.photoDropzone.classList.remove('hidden');
        
        // Reset state related to photo
        this.state.convertedWebpData = null;
        this.state.hasExifData = false;
        if (this.elements.previewImg) this.elements.previewImg.src = ''; // Clear preview image source
        
        // Clear any photo errors using helpers
        this.helpers.clearFieldError(this.elements, 'photo');
    },

    applyExifData: function(result) {
        this.state.hasExifData = false; // Reset flag
        
        if (result.error || !this.elements.exifDataDiv) {
            console.warn('EXIF data error or elements missing:', result.error);
            if (this.elements.exifDataDiv) this.elements.exifDataDiv.classList.add('hidden');
            return;
        }
        
        const exifData = result.exifData;
        const gpsCoordinates = result.gpsCoordinates;
        
        this.elements.exifDataDiv.classList.add('hidden'); // Hide initially
        if (this.elements.exifDate) this.elements.exifDate.textContent = 'Nicht verfügbar';
        if (this.elements.exifLocation) this.elements.exifLocation.textContent = 'Nicht verfügbar';

        // Process date
        if (exifData?.dateTime && this.elements.sightingDateInput) {
            const parts = exifData.dateTime.split(' ')[0].split(':');
            if (parts.length === 3) {
                const formattedDate = `${parts[0]}-${parts[1]}-${parts[2]}`;
                // Check if date is valid before setting
                const dateObj = new Date(formattedDate);
                if (!isNaN(dateObj)) {
                     // Prevent setting future dates from EXIF
                     const today = new Date();
                     today.setHours(0, 0, 0, 0);
                     if (dateObj <= today) {
                        this.elements.sightingDateInput.value = formattedDate;
                        if (this.elements.exifDate) {
                            this.elements.exifDate.textContent = dateObj.toLocaleDateString('de-DE');
                        }
                        this.state.hasExifData = true;
                     } else {
                         console.warn('EXIF date is in the future, ignoring:', formattedDate);
                     }
                } else {
                    console.warn('Invalid date parsed from EXIF:', exifData.dateTime);
                }
            }
        }
        
        // Process GPS coordinates
        if (gpsCoordinates && this.elements.latInput && this.elements.lngInput) {
            const { lat, lng } = gpsCoordinates;
            
            this.elements.latInput.value = lat;
            this.elements.lngInput.value = lng;
            if (this.elements.manualLatInput) this.elements.manualLatInput.value = lat.toFixed(6);
            if (this.elements.manualLngInput) this.elements.manualLngInput.value = lng.toFixed(6);
            if (this.elements.exifLocation) {
                this.elements.exifLocation.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            }
            
            // Trigger map update using the callback
            if (typeof this.mapUpdateCallback === 'function') {
                 this.mapUpdateCallback(lat, lng);
            } else {
                 console.warn('Map update callback function not provided to PhotoHandler.');
            }

            this.state.hasExifData = true;
        }
        
        // Show EXIF panel only if we actually extracted usable data
        if (this.state.hasExifData) {
            this.elements.exifDataDiv.classList.remove('hidden');
        }
    }
}; 