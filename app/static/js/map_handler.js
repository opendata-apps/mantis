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
        
        // Check if Leaflet is loaded
        if (typeof L === 'undefined') {
            console.error('Leaflet library (L) not loaded.');
             this.helpers.showFieldError(this.elements, 'map', 'Kartenbibliothek konnte nicht geladen werden.');
            return;
        }

        try {
            this.state.map = L.map(this.elements.mapContainer, {
                zoomControl: true,
                attributionControl: false, // Managed manually if needed
                fadeAnimation: false, // Can improve performance on some systems
                zoomAnimation: true
            }).setView(this.config.mapDefaults.center, this.config.mapDefaults.zoom);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
                maxZoom: 18,
                minZoom: 3
            }).addTo(this.state.map);

            // Add Geocoder control if library is loaded
             if (typeof L.Control.Geocoder !== 'undefined') {
                this.state.geocoder = L.Control.geocoder({
                    defaultMarkGeocode: false,
                    placeholder: 'Nach Adresse suchen...',
                    errorMessage: 'Adresse nicht gefunden'
                })
                .on('markgeocode', this.handleGeocodeResult.bind(this))
                .addTo(this.state.map);
             } else {
                 console.warn('Leaflet Geocoder library not loaded.');
             }

            // Add simple Locate control
            if (typeof L.Control.Locate !== 'undefined') {
                L.control.locate().addTo(this.state.map);
                
                // Only zoom to GPS location, don't set marker (force manual placement)
                this.state.map.on('locationfound', (e) => {
                    this.state.map.setView(e.latlng, this.config.mapDefaults.sightingZoom);
                    // Show message to encourage manual marker placement
                    this.helpers.showFieldError(this.elements, 'coordinates', '📍 GPS-Position gefunden. Bitte klicken Sie auf die Karte, um den genauen Fundort zu markieren.');
                });
            }

            // Add map event listeners
            this.state.map.on('click', this.handleMapClick.bind(this));

            // Add manual input listeners
            if (this.elements.manualLatInput) this.elements.manualLatInput.addEventListener('change', this.updateMapFromManualInput.bind(this));
            if (this.elements.manualLngInput) this.elements.manualLngInput.addEventListener('change', this.updateMapFromManualInput.bind(this));
            
            // Initial check if coordinates already exist (e.g., from server-side validation error)
            this.updateMarkerFromForm();

        } catch (error) {
            console.error("Error initializing Leaflet map:", error);
            this.helpers.showFieldError(this.elements, 'map', 'Karte konnte nicht initialisiert werden.');
        }
    },
    
    // Check form fields and update marker if values exist
    updateMarkerFromForm: function() {
        const lat = parseFloat(this.elements.latInput?.value);
        const lng = parseFloat(this.elements.lngInput?.value);
        if (!isNaN(lat) && !isNaN(lng)) {
            this.setMarkerAndCoordinates(lat, lng, false); // Don't trigger reverse geocode initially
            // Center map if we found coordinates
             if (this.state.map) {
                 this.state.map.setView([lat, lng], this.config.mapDefaults.sightingZoom);
             }
        }
    },

    handleMapClick: function(e) {
        const now = Date.now();
        if (now - this.state.lastMapClick < 500) return; // Debounce clicks
        this.state.lastMapClick = now;
        
        this.setMarkerAndCoordinates(e.latlng.lat, e.latlng.lng);
        // Clear any coordinate placement messages since user manually placed marker
        this.helpers.clearFieldError(this.elements, 'coordinates');
    },

    handleGeocodeResult: function(e) {
        if (e.geocode && e.geocode.center) {
            const latlng = e.geocode.center;
            // Only zoom to search result, don't set marker (force manual placement)
            if (this.state.map && e.geocode.bbox) {
                this.state.map.fitBounds(e.geocode.bbox);
            } else {
                this.state.map.setView([latlng.lat, latlng.lng], this.config.mapDefaults.sightingZoom);
            }
            // Show message to encourage manual marker placement
            this.helpers.showFieldError(this.elements, 'coordinates', '🔍 Adresse gefunden. Bitte klicken Sie auf die Karte, um den genauen Fundort zu markieren.');
        } else {
            console.warn('Geocode result did not contain center coordinates:', e);
            this.helpers.showFieldError(this.elements, 'map', 'Adresse gefunden, aber Koordinaten fehlen.');
        }
    },

    setMarkerAndCoordinates: function(lat, lng, triggerReverseGeocode = true) {
        if (!this.state.map) return;

        // Clamp coordinates to valid ranges just in case
        lat = Math.max(-90, Math.min(90, lat));
        lng = Math.max(-180, Math.min(180, lng));
        
        // Update marker
        if (this.state.marker) {
            this.state.marker.setLatLng([lat, lng]);
        } else {
            this.state.marker = L.marker([lat, lng], { draggable: true })
                                .addTo(this.state.map)
                                .on('dragend', this.handleMarkerDrag.bind(this));
        }
        
        // Update form fields (hidden and manual)
        if (this.elements.latInput) this.elements.latInput.value = lat.toFixed(6);
        if (this.elements.lngInput) this.elements.lngInput.value = lng.toFixed(6);
        if (this.elements.manualLatInput) this.elements.manualLatInput.value = lat.toFixed(6);
        if (this.elements.manualLngInput) this.elements.manualLngInput.value = lng.toFixed(6);
        
        // Clear any previous coordinate errors
        this.helpers.clearFieldError(this.elements, 'coordinates');
        
        // Trigger reverse geocoding (unless called from initial load or EXIF)
        if (triggerReverseGeocode) {
             clearTimeout(this.state.geocodeDebounceTimer);
             this.state.geocodeDebounceTimer = setTimeout(() => {
                 this.reverseGeocode(lat, lng);
             }, 300); // Debounce reverse geocoding calls
        }
    },

    handleMarkerDrag: function(e) {
        const marker = e.target;
        const position = marker.getLatLng();
        this.setMarkerAndCoordinates(position.lat, position.lng);
    },

    updateMapFromManualInput: function() {
        const lat = parseFloat(this.elements.manualLatInput?.value);
        const lng = parseFloat(this.elements.manualLngInput?.value);
        
        if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
            // Update the marker and hidden fields, trigger reverse geocode
            this.setMarkerAndCoordinates(lat, lng);
            
            // Center map on new coordinates
            if (this.state.map) {
                this.state.map.setView([lat, lng], this.state.map.getZoom());
            }
        } else {
            this.helpers.showFieldError(this.elements, 'coordinates', 'Ungültige Koordinaten.');
        }
    },
    
    // This function is called externally (e.g., by PhotoHandler via window)
    updateMapWithCoordinates: function(lat, lng) {
        if (!this.state.map || isNaN(lat) || isNaN(lng)) return;
        
        // Short delay ensures map container is visible and sized correctly
        setTimeout(() => {
            try {
                this.state.map.invalidateSize(); // Recalculate map size
                this.state.map.setView([lat, lng], this.config.mapDefaults.sightingZoom);
                // Update marker but DON'T trigger reverse geocode (data came from EXIF)
                this.setMarkerAndCoordinates(lat, lng, false); 
                // Try reverse geocoding EXIF coords anyway to potentially fill address fields
                this.reverseGeocode(lat, lng);
            } catch(error) {
                console.error("Error updating map view/marker:", error);
            }
        }, 100);
    },

    reverseGeocode: async function(lat, lng) {
        if (!this.elements.addressFields) return;

        this.showAddressLoading(true);
        this.helpers.clearFieldError(this.elements, 'coordinates'); // Clear previous errors

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1&accept-language=de`,
                { headers: { 'Accept-Language': 'de' } }
            );
            
            if (!response.ok) {
                throw new Error(`Nominatim API error: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data && data.address) {
                this.applyReverseGeocodeResult(data.address);
            } else {
                console.warn("Reverse geocoding returned no address details for:", lat, lng, data);
                // Don't show an error if coordinates are valid but address is simply not found
                // this.helpers.showFieldError(elements, 'coordinates', 'Keine Adressdetails gefunden.');
            }
        } catch (error) {
            console.error('Error during reverse geocoding:', error);
            this.helpers.showFieldError(this.elements, 'coordinates', 'Adressdetails konnten nicht abgerufen werden.');
        } finally {
            this.showAddressLoading(false);
        }
    },

    applyReverseGeocodeResult: function(address) {
        const fields = this.elements.addressFields;
        if (!fields) return;

        // Use || '' to ensure fields are cleared if address part is missing
        if (fields.zipCode) fields.zipCode.value = address.postcode || '';
        if (fields.city) fields.city.value = address.city || address.town || address.village || address.hamlet || '';
        if (fields.state) fields.state.value = address.state || '';
        if (fields.district) fields.district.value = address.county || ''; 
        if (fields.street) {
            let street = address.road || '';
            if (address.house_number) {
                street += ' ' + address.house_number;
            }
            fields.street.value = street.trim();
        }
        // Clear errors on specific address fields if they were previously shown
         Object.keys(fields).forEach(key => {
              if (fields[key]?.id) {
                 this.helpers.clearFieldError(this.elements, fields[key].id);
              }
         });
    },

    showAddressLoading: function(isLoading) {
        if (!this.elements.addressFields) return;
        const fields = Object.values(this.elements.addressFields).filter(Boolean);
        
        fields.forEach(field => {
            field.disabled = isLoading;
            field.style.backgroundColor = isLoading ? '#f8f9fa' : ''; // Subtle background indication
        });
    }
}; 