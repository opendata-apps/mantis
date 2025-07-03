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
        
        // Click handler for the dropzone
        this.elements.photoDropzone.addEventListener('click', () => {
            this.elements.photoInput.click();
        });
        
        if (this.elements.removePhotoBtn) {
            this.elements.removePhotoBtn.addEventListener('click', this.removePhoto.bind(this));
        }
    },

    handleDragOver: function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('dragover');
    },

    handleDragLeave: function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
    },

    handleDrop: function(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            this.elements.photoInput.files = e.dataTransfer.files;
            const changeEvent = new Event('change', { bubbles: true });
            this.elements.photoInput.dispatchEvent(changeEvent);
        }
    },

    handlePhotoChange: async function(event) {
        const inputElement = event.target;
        if (!inputElement.files || !inputElement.files[0]) return;
        
        const file = inputElement.files[0];
        
        // Quick validation first
        if (!this.helpers.isValidImageType(file)) {
            this.helpers.showFieldError(this.elements, 'photo', 'Bitte wählen Sie eine Bilddatei (JPG, PNG, WEBP, HEIC oder HEIF).');
            return;
        }
        
        if (!this.helpers.isValidImageSize(file)) {
            this.helpers.showFieldError(this.elements, 'photo', 'Das Bild muss kleiner als 12MB sein.');
            return;
        }
        
        // Clear any previous errors
        this.helpers.clearFieldError(this.elements, 'photo');
        
        // Start processing with progress feedback
        await this.processImageWithProgress(file);
    },

    processImageWithProgress: async function(file) {
        if (!file) {
            this.helpers.showFieldError(this.elements, 'photo', 'Keine Datei ausgewählt.');
            return;
        }

        const originalFileName = file.name || 'unknown.jpg';
        let loadingTimeout = null;
        
        try {
            // Set a maximum timeout for the entire process (15 seconds)
            loadingTimeout = setTimeout(() => {
                console.error('Image processing timeout - hiding loading indicator');
                this.helpers.showDropzoneLoading(this.elements, false);
                this.handleProcessingError(new Error('Bildverarbeitung hat zu lange gedauert. Bitte versuchen Sie es erneut.'));
            }, 15000);
            
            // Step 1: Initial validation and setup
            this.helpers.showDropzoneLoading(this.elements, true, "Bereite Bildverarbeitung vor...");
            await this.delay(100);
            
            // Step 2: EXIF processing (non-blocking) - do this first with original file
            this.helpers.showDropzoneLoading(this.elements, true, "Lese Bildinformationen...");
            await this.delay(100);
            const exifResult = await this.processExifNonBlocking(file);
            
            // Check if EXIF extraction timed out or failed
            if (exifResult && exifResult.timedOut) {
                console.warn('EXIF extraction timed out, continuing without metadata');
            }
            
            // Step 3: Image conversion and optimization (WebP converter handles HEIC internally)
            this.helpers.showDropzoneLoading(this.elements, true, "Optimiere Bild für Upload...");
            await this.delay(100);
            
            // Ensure file has original filename for WebP converter
            if (!file.name && originalFileName) {
                file.originalFileName = originalFileName;
            }
            
            const webpResult = await this.convertToWebpNonBlocking(file);
            
            // Step 4: Finalize
            this.helpers.showDropzoneLoading(this.elements, true, "Fertigstellung...");
            await this.delay(100);
            
            // Validate results before storing
            if (!webpResult || !webpResult.blob || !webpResult.dataUrl) {
                throw new Error('Bildkonvertierung unvollständig - bitte versuchen Sie es erneut.');
            }
            
            // Store WebP data in main state
            this.state.convertedWebpData = {
                dataUrl: webpResult.dataUrl,
                blob: webpResult.blob,
                originalFileName: webpResult.originalFileName || originalFileName
            };
            
            // Display preview and apply EXIF data
            this.displayPhotoPreview(webpResult.dataUrl);
            this.applyExifData(exifResult);
            
        } catch (error) {
            console.error('Error processing image:', error);
            this.handleProcessingError(error);
        } finally {
            // Clear the timeout if it hasn't fired
            if (loadingTimeout) {
                clearTimeout(loadingTimeout);
            }
            // Always hide the loading indicator
            this.helpers.showDropzoneLoading(this.elements, false);
        }
    },

    // Simple delay function to allow UI updates
    delay: function(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },



    processExifNonBlocking: async function(file) {
        return new Promise((resolve) => {
            // Use setTimeout to make EXIF processing non-blocking
            setTimeout(async () => {
                try {
                    const result = await ExifProcessor.processImageExif(file);
                    resolve(result);
                } catch (err) {
                    console.error("EXIF Error:", err);
                    resolve({ error: err.message });
                }
            }, 10);
        });
    },

    convertToWebpNonBlocking: async function(file) {
        return new Promise((resolve, reject) => {
            // Use setTimeout to make WebP conversion non-blocking
            setTimeout(async () => {
                try {
                    const result = await WebpConverter.processImage(file);
                    resolve(result);
                } catch (err) {
                    reject(new Error(`Bildkonvertierung fehlgeschlagen: ${err.message}`));
                }
            }, 10);
        });
    },

    handleProcessingError: function(error) {
        let errorMessage = 'Ein Fehler ist beim Verarbeiten des Bildes aufgetreten.';
        
        if (error.message.includes('HEIC')) {
            errorMessage = 'HEIC/HEIF Bilder konnten nicht verarbeitet werden. Bitte konvertieren Sie das Bild zu JPEG oder PNG vor dem Hochladen.';
        } else if (error.message.includes('load image')) {
            errorMessage = 'Das Bild konnte nicht geladen werden. Bitte versuchen Sie ein anderes Bild.';
        } else if (error.message.includes('Bildkonvertierung')) {
            errorMessage = error.message;
        } else if (error.message.includes('too large') || error.message.includes('size')) {
            errorMessage = 'Das Bild ist zu groß. Bitte wählen Sie ein kleineres Bild (max. 12MB).';
        }
        
        this.helpers.showFieldError(this.elements, 'photo', errorMessage);
        this.removePhoto();
    },

    displayPhotoPreview: function(dataUrl) {
        if (!this.elements.photoPreview || !this.elements.previewImg) return;
        
        this.elements.photoDropzone.classList.add('hidden');
        this.elements.photoPreview.classList.remove('hidden');
        this.elements.previewImg.src = dataUrl;
    },

    removePhoto: function() {
        if (!this.elements.photoInput) return;
        
        this.elements.photoInput.value = '';
        
        if (this.elements.photoPreview) this.elements.photoPreview.classList.add('hidden');
        if (this.elements.exifDataDiv) this.elements.exifDataDiv.classList.add('hidden');
        if (this.elements.photoDropzone) this.elements.photoDropzone.classList.remove('hidden');
        
        // Reset state related to photo
        this.state.convertedWebpData = null;
        this.state.hasExifData = false;
        if (this.elements.previewImg) this.elements.previewImg.src = '';
        
        this.helpers.clearFieldError(this.elements, 'photo');
    },

    applyExifData: function(result) {
        this.state.hasExifData = false;
        
        // Handle timeout, error, or missing result gracefully
        if (!result || result.error || result.timedOut || !this.elements.exifDataDiv) {
            if (result && result.timedOut) {
                console.warn('EXIF extraction timed out - continuing without metadata');
            } else if (result && result.error) {
                console.warn('EXIF data error:', result.error);
            }
            if (this.elements.exifDataDiv) this.elements.exifDataDiv.classList.add('hidden');
            return;
        }
        
        const exifData = result.exifData;
        const gpsCoordinates = result.gpsCoordinates;
        
        this.elements.exifDataDiv.classList.add('hidden');
        if (this.elements.exifDate) this.elements.exifDate.textContent = 'Nicht verfügbar';
        if (this.elements.exifLocation) this.elements.exifLocation.textContent = 'Nicht verfügbar';

        // Process date
        if (exifData?.dateTime && this.elements.sightingDateInput) {
            const parts = exifData.dateTime.split(' ')[0].split(':');
            if (parts.length === 3) {
                const formattedDate = `${parts[0]}-${parts[1]}-${parts[2]}`;
                const dateObj = new Date(formattedDate);
                if (!isNaN(dateObj)) {
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