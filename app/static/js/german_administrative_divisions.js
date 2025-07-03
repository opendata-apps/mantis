/**
 * German Administrative Divisions Handler
 * Manages the complex logic for German states, city-states, and districts
 */
const GermanAdministrativeDivisions = {
    // Constants for German administrative types
    CITY_STATES: {
        BERLIN: 'Berlin',
        HAMBURG: 'Hamburg', 
        BREMEN: 'Bremen'
    },
    
    /**
     * Determines if a location is in a German city-state
     * @param {Object} address - Nominatim address object
     * @returns {boolean}
     */
    isCityState: function(address) {
        const cityStates = Object.values(this.CITY_STATES);
        
        return cityStates.includes(address.city) || 
               address.city === this.BREMEN_ALTERNATE_NAME ||
               (address.state === this.CITY_STATES.BREMEN && 
                address.city === this.CITY_STATES.BREMEN);
    },
    
    /**
     * Gets the appropriate state name for city-states
     * @param {Object} address - Nominatim address object
     * @returns {string}
     */
    getCityStateName: function(address) {
        // Bremen sometimes has state field populated
        if (address.state === this.CITY_STATES.BREMEN) {
            return this.CITY_STATES.BREMEN;
        }
        return address.city;
    },
    
    /**
     * Gets the district/borough for city-states
     * @param {Object} address - Nominatim address object
     * @returns {string}
     */
    getCityStateDistrict: function(address) {
        // Priority order based on what each city-state typically uses
        return address.borough || address.city_district || address.suburb || '';
    },
    
    /**
     * Checks if a city is a kreisfreie Stadt (independent city)
     * Kreisfreie Städte are identified by having no county in the geocoding result
     * @param {Object} address - Nominatim address object
     * @returns {boolean}
     */
    isKreisfreieStadt: function(address) {
        // A city is kreisfreie if it has no county and is not a village/hamlet
        // This works because kreisfreie Städte handle their own administration
        return !address.county && 
               (address.city || address.town) && 
               !address.village && 
               !address.hamlet;
    },
    
    /**
     * Processes address for German administrative divisions
     * @param {Object} address - Nominatim address object
     * @returns {Object} Processed state and district values
     */
    processAddress: function(address) {
        if (this.isCityState(address)) {
            return {
                state: this.getCityStateName(address),
                district: this.getCityStateDistrict(address)
            };
        }
        
        // Regular handling for non city-states
        return {
            state: address.state || '',
            district: this.getDistrict(address)
        };
    },
    
    /**
     * Gets the district for non city-state locations
     * @param {Object} address - Nominatim address object
     * @returns {string}
     */
    getDistrict: function(address) {
        // If there's a county, use it
        if (address.county) {
            return address.county;
        }
        
        // If no county but it's a city/town (kreisfreie Stadt), use the city name
        if (this.isKreisfreieStadt(address)) {
            return address.city || address.town || '';
        }
        
        return '';
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GermanAdministrativeDivisions;
}