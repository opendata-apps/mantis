const MapHandler = {
    initialize: function(state, elements, config, helpers) {
        this.state = state;
        this.elements = elements;
        this.config = config;
        this.helpers = helpers;
        this.initMapInstance();
    },

    initMapInstance: function() {
        if (!this.elements.mapContainer) {
            console.error("Map container not found.");
            return;
        }
        
        if (typeof L === 'undefined') {
            console.error('Leaflet library not loaded.');
            this.helpers.showFieldError(this.elements, 'map', 'Kartenbibliothek konnte nicht geladen werden.');
            return;
        }

        try {
            this.state.map = L.map(this.elements.mapContainer, {
                zoomControl: true,
                attributionControl: false,
                fadeAnimation: false,
                zoomAnimation: true
            }).setView(this.config.mapDefaults.center, this.config.mapDefaults.zoom);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
                maxZoom: 18,
                minZoom: 3
            }).addTo(this.state.map);

            this.initGeocoder();
            this.initLocationControl();
            this.initEventListeners();
            this.updateMarkerFromForm();

        } catch (error) {
            console.error("Error initializing map:", error);
            this.helpers.showFieldError(this.elements, 'map', 'Karte konnte nicht initialisiert werden.');
        }
    },

    initGeocoder: function() {
        if (typeof L.Control.Geocoder === 'undefined') {
            console.warn('Geocoder library not loaded.');
            return;
        }

        this.state.geocoder = L.Control.geocoder({
            defaultMarkGeocode: false,
            placeholder: 'Nach Adresse suchen...',
            errorMessage: 'Adresse nicht gefunden'
        })
        .on('markgeocode', this.handleGeocodeResult.bind(this))
        .addTo(this.state.map);
    },

    initLocationControl: function() {
        if (typeof L.Control.Locate === 'undefined') return;

        this.state.locateControl = L.control.locate({
            watch: true,
            setView: false,
            keepCurrentZoomLevel: true,
            drawCircle: false,
            drawMarker: false,
            showPopup: false,
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 30000,
            strings: { title: "Meinen Standort anzeigen" }
        }).addTo(this.state.map);
        
        this.resetLocationTracking();
        
        this.state.map.on('locationfound', (e) => {
            this.handleLocationFound(e);
        });
        
        this.state.map.on('locationerror', (e) => {
            console.warn('Location error:', e.message);
            this.stopLocationUpdates();
        });
    },

    initEventListeners: function() {
        this.state.map.on('click', this.handleMapClick.bind(this));
        
        if (this.elements.manualLatInput) {
            this.elements.manualLatInput.addEventListener('change', this.updateMapFromManualInput.bind(this));
        }
        if (this.elements.manualLngInput) {
            this.elements.manualLngInput.addEventListener('change', this.updateMapFromManualInput.bind(this));
        }
    },
    resetLocationTracking: function() {
        this.state.locationUpdateCount = 0;
        this.state.bestAccuracy = Infinity;
        this.state.locationTimeout = null;
    },

    handleLocationFound: function(e) {
        this.state.locationUpdateCount++;
        const accuracy = e.accuracy || Infinity;
        
        if (accuracy < this.state.bestAccuracy || this.state.locationUpdateCount === 1) {
            this.state.bestAccuracy = accuracy;
            this.state.map.setView(e.latlng, this.config.mapDefaults.sightingZoom);
            
            const message = this.buildLocationMessage(accuracy);
            this.helpers.showFieldError(this.elements, 'coordinates', message);
        }
        
        if (accuracy < 50 || this.state.locationUpdateCount >= 5) {
            this.stopLocationUpdates();
        } else if (!this.state.locationTimeout) {
            this.state.locationTimeout = setTimeout(() => {
                this.stopLocationUpdates();
            }, 10000);
        }
    },

    buildLocationMessage: function(accuracy) {
        let message = '📍 GPS-Position gefunden';
        if (accuracy > 1000) {
            message += ' (ungefähr)';
        } else if (accuracy > 100) {
            message += ' (ca. ' + Math.round(accuracy) + 'm genau)';
        } else {
            message += ' (präzise)';
        }
        return message + '. Bitte klicken Sie auf die Karte, um den genauen Fundort zu markieren.';
    },

    updateMarkerFromForm: function() {
        const lat = parseFloat(this.elements.latInput?.value);
        const lng = parseFloat(this.elements.lngInput?.value);
        if (!isNaN(lat) && !isNaN(lng)) {
            this.setMarkerAndCoordinates(lat, lng, false);
            if (this.state.map) {
                this.state.map.setView([lat, lng], this.config.mapDefaults.sightingZoom);
            }
        }
    },

    handleMapClick: function(e) {
        const now = Date.now();
        if (now - this.state.lastMapClick < 500) return;
        this.state.lastMapClick = now;
        
        this.setMarkerAndCoordinates(e.latlng.lat, e.latlng.lng);
        this.helpers.clearFieldError(this.elements, 'coordinates');
    },

    handleGeocodeResult: function(e) {
        if (!e.geocode?.center) {
            console.warn('Invalid geocode result:', e);
            this.helpers.showFieldError(this.elements, 'map', 'Adresse gefunden, aber Koordinaten fehlen.');
            return;
        }

        const latlng = e.geocode.center;
        if (e.geocode.bbox) {
            this.state.map.fitBounds(e.geocode.bbox);
        } else {
            this.state.map.setView([latlng.lat, latlng.lng], this.config.mapDefaults.sightingZoom);
        }
        
        this.helpers.showFieldError(this.elements, 'coordinates', 
            '🔍 Adresse gefunden. Bitte klicken Sie auf die Karte, um den genauen Fundort zu markieren.');
    },

    setMarkerAndCoordinates: function(lat, lng, triggerReverseGeocode = true) {
        if (!this.state.map) return;

        lat = Math.max(-90, Math.min(90, lat));
        lng = Math.max(-180, Math.min(180, lng));
        
        this.updateMarker(lat, lng);
        this.updateFormFields(lat, lng);
        this.helpers.clearFieldError(this.elements, 'coordinates');
        
        if (triggerReverseGeocode) {
            clearTimeout(this.state.geocodeDebounceTimer);
            this.state.geocodeDebounceTimer = setTimeout(() => {
                this.reverseGeocode(lat, lng);
            }, 300);
        }
    },

    updateMarker: function(lat, lng) {
        if (this.state.marker) {
            this.state.marker.setLatLng([lat, lng]);
        } else {
            this.state.marker = L.marker([lat, lng], { draggable: true })
                                .addTo(this.state.map)
                                .on('dragend', this.handleMarkerDrag.bind(this));
        }
    },

    updateFormFields: function(lat, lng) {
        const latStr = lat.toFixed(6);
        const lngStr = lng.toFixed(6);
        
        if (this.elements.latInput) this.elements.latInput.value = latStr;
        if (this.elements.lngInput) this.elements.lngInput.value = lngStr;
        if (this.elements.manualLatInput) this.elements.manualLatInput.value = latStr;
        if (this.elements.manualLngInput) this.elements.manualLngInput.value = lngStr;
    },

    handleMarkerDrag: function(e) {
        const position = e.target.getLatLng();
        this.setMarkerAndCoordinates(position.lat, position.lng);
    },

    updateMapFromManualInput: function() {
        const lat = parseFloat(this.elements.manualLatInput?.value);
        const lng = parseFloat(this.elements.manualLngInput?.value);
        
        if (this.isValidCoordinate(lat, lng)) {
            this.setMarkerAndCoordinates(lat, lng);
            if (this.state.map) {
                this.state.map.setView([lat, lng], this.state.map.getZoom());
            }
        } else {
            this.helpers.showFieldError(this.elements, 'coordinates', 'Ungültige Koordinaten.');
        }
    },

    isValidCoordinate: function(lat, lng) {
        return !isNaN(lat) && !isNaN(lng) && 
               lat >= -90 && lat <= 90 && 
               lng >= -180 && lng <= 180;
    },
    updateMapWithCoordinates: function(lat, lng) {
        if (!this.state.map || isNaN(lat) || isNaN(lng)) return;
        
        setTimeout(() => {
            try {
                this.state.map.invalidateSize();
                this.state.map.setView([lat, lng], this.config.mapDefaults.sightingZoom);
                this.setMarkerAndCoordinates(lat, lng, false);
                this.reverseGeocode(lat, lng);
            } catch(error) {
                console.error("Error updating map:", error);
            }
        }, 100);
    },

    reverseGeocode: async function(lat, lng) {
        if (!this.elements.addressFields) return;

        this.showAddressLoading(true);
        this.helpers.clearFieldError(this.elements, 'coordinates');

        try {
            const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=de`;
            const response = await fetch(url, { 
                headers: { 'Accept-Language': 'de' } 
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data?.address) {
                this.applyReverseGeocodeResult(data.address);
            } else {
                console.warn("No address details found for:", lat, lng);
            }
        } catch (error) {
            console.error('Reverse geocoding error:', error);
            this.helpers.showFieldError(this.elements, 'coordinates', 'Adressdetails konnten nicht abgerufen werden.');
        } finally {
            this.showAddressLoading(false);
        }
    },

    applyReverseGeocodeResult: function(address) {
        const fields = this.elements.addressFields;
        if (!fields) return;

        // Process German administrative divisions
        const administrativeDivisions = GermanAdministrativeDivisions.processAddress(address);
        
        // Batch update all fields at once for better performance
        this.updateAddressFields({
            zipCode: address.postcode || '',
            city: this.extractCityName(address),
            state: administrativeDivisions.state,
            district: administrativeDivisions.district,
            street: this.formatStreetAddress(address)
        });
        
        // Clear any existing field errors
        this.clearAllFieldErrors();
    },
    
    /**
     * Extracts city name from various possible fields
     * @private
     */
    extractCityName: function(address) {
        return address.city || address.town || address.village || address.hamlet || '';
    },
    
    /**
     * Formats street address with house number
     * @private
     */
    formatStreetAddress: function(address) {
        if (!address.road) return '';
        
        return address.house_number 
            ? `${address.road} ${address.house_number}`.trim()
            : address.road;
    },
    
    /**
     * Updates all address fields efficiently
     * @private
     */
    updateAddressFields: function(values) {
        const fields = this.elements.addressFields;
        if (!fields) return;
        
        // Update only fields that exist and have changed
        const fieldMap = {
            zipCode: 'zipCode',
            city: 'city',
            state: 'state',
            district: 'district',
            street: 'street'
        };
        
        for (const [key, fieldName] of Object.entries(fieldMap)) {
            const field = fields[fieldName];
            if (field && field.value !== values[key]) {
                field.value = values[key];
            }
        }
    },
    
    /**
     * Clears all field errors efficiently
     * @private
     */
    clearAllFieldErrors: function() {
        const fields = this.elements.addressFields;
        if (!fields || !this.helpers) return;
        
        // Use for...of for better performance than Object.keys().forEach()
        for (const field of Object.values(fields)) {
            if (field?.id) {
                this.helpers.clearFieldError(this.elements, field.id);
            }
        }
    },

    showAddressLoading: function(isLoading) {
        if (!this.elements.addressFields) return;
        
        const fields = Object.values(this.elements.addressFields).filter(Boolean);
        fields.forEach(field => {
            field.disabled = isLoading;
            field.style.backgroundColor = isLoading ? '#f8f9fa' : '';
        });
    },

    stopLocationUpdates: function() {
        if (this.state.locateControl) {
            this.state.locateControl.stop();
        }
        if (this.state.locationTimeout) {
            clearTimeout(this.state.locationTimeout);
            this.state.locationTimeout = null;
        }
    },

    autoRequestLocationIfNeeded: function() {
        const lat = parseFloat(this.elements.latInput?.value);
        const lng = parseFloat(this.elements.lngInput?.value);
        
        if (isNaN(lat) || isNaN(lng)) {
            if (navigator.geolocation && this.state.locateControl && this.state.map) {
                this.resetLocationTracking();
                this.state.locateControl.start();
            }
        }
    },

    /**
     * @deprecated Removed - kreisfreie Stadt detection is now automatic
     */
    isKreisfreieStadt: function() {
        console.warn('isKreisfreieStadt is deprecated. Kreisfreie Stadt detection is now automatic based on geocoding data.');
        return false;
    }
}; 