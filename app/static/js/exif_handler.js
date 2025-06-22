/**
 * exif_handler.js
 * Handles extraction and processing of EXIF data from images
 * Works in conjunction with exif.js library
 */

/**
 * Extract EXIF data from an image file
 * @param {File} file - The image file to extract EXIF data from
 * @returns {Promise} - A promise that resolves with EXIF data object
 */
function extractExifData(file) {
    return new Promise((resolve, reject) => {
        try {
            // Check if EXIF.js is available
            if (typeof EXIF === 'undefined') {
                return reject(new Error('EXIF.js library not loaded'));
            }

            // Read the file
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const result = e.target.result;
                
                // Extract EXIF data
                EXIF.getData(file, function() {
                    const exifData = {
                        make: EXIF.getTag(this, 'Make'),
                        model: EXIF.getTag(this, 'Model'),
                        dateTime: EXIF.getTag(this, 'DateTime'),
                        gpsLatitude: EXIF.getTag(this, 'GPSLatitude'),
                        gpsLongitude: EXIF.getTag(this, 'GPSLongitude'),
                        gpsLatitudeRef: EXIF.getTag(this, 'GPSLatitudeRef'),
                        gpsLongitudeRef: EXIF.getTag(this, 'GPSLongitudeRef'),
                        orientation: EXIF.getTag(this, 'Orientation'),
                        allTags: EXIF.getAllTags(this)
                    };
                    
                    resolve(exifData);
                });
            };
            
            reader.onerror = function(error) {
                reject(error);
            };
            
            // Read the file as an array buffer (binary data)
            reader.readAsArrayBuffer(file);
        } catch (error) {
            reject(error);
        }
    });
}

/**
 * Convert GPS coordinates from EXIF format to decimal degrees
 * @param {Array} coordinates - Coordinates array from EXIF data
 * @param {String} ref - Direction reference (N, S, E, W)
 * @returns {Number} - Decimal degrees
 */
function convertToDecimalDegrees(coordinates, ref) {
    if (!coordinates) return null;
    
    // EXIF coordinates are in [degrees, minutes, seconds] format
    const degrees = coordinates[0];
    const minutes = coordinates[1];
    const seconds = coordinates[2];
    
    let dd = degrees + (minutes / 60) + (seconds / 3600);
    
    // If southern or western hemisphere, negate the value
    if (ref === 'S' || ref === 'W') {
        dd = -dd;
    }
    
    return dd;
}

/**
 * Extract GPS coordinates from EXIF data and convert to decimal degrees
 * @param {Object} exifData - EXIF data object
 * @returns {Object|null} - Object with lat/lng properties or null if no GPS data
 */
function extractGpsCoordinates(exifData) {
    if (!exifData || !exifData.gpsLatitude || !exifData.gpsLongitude) {
        return null;
    }
    
    const lat = convertToDecimalDegrees(exifData.gpsLatitude, exifData.gpsLatitudeRef);
    const lng = convertToDecimalDegrees(exifData.gpsLongitude, exifData.gpsLongitudeRef);
    
    if (lat && lng) {
        return { lat, lng };
    }
    
    return null;
}

/**
 * Process an image file to extract EXIF data and handle GPS coordinates
 * @param {File} file - The image file to process
 * @returns {Promise} - A promise that resolves with processed data object
 */
function processImageExif(file) {
    return extractExifData(file)
        .then(exifData => {
            const gpsCoordinates = extractGpsCoordinates(exifData);
            return {
                exifData,
                gpsCoordinates
            };
        })
        .catch(error => {
            console.error('Error processing EXIF data:', error);
            return {
                exifData: null,
                gpsCoordinates: null,
                error: error.message
            };
        });
}

const ExifProcessor = {
    processImageExif: async function(file) {
        return new Promise((resolve, reject) => {
            if (!file) {
                return reject(new Error("No file provided."));
            }

            // Check if EXIF library is loaded
            if (typeof EXIF === 'undefined') {
                console.warn('EXIF.js library not loaded.');
                // Resolve with no data instead of rejecting, 
                // as missing EXIF is not a fatal error for the form.
                return resolve({ exifData: null, gpsCoordinates: null }); 
            }

            try {
                EXIF.getData(file, function() {
                    const exifData = EXIF.getAllTags(this);
                    let gpsCoordinates = null;

                    // Extract GPS coordinates if available
                    const lat = EXIF.getTag(this, "GPSLatitude");
                    const lon = EXIF.getTag(this, "GPSLongitude");
                    const latRef = EXIF.getTag(this, "GPSLatitudeRef");
                    const lonRef = EXIF.getTag(this, "GPSLongitudeRef");

                    if (lat && lon && latRef && lonRef) {
                        try {
                            const latitude = ExifProcessor.convertDMSToDD(lat[0], lat[1], lat[2], latRef);
                            const longitude = ExifProcessor.convertDMSToDD(lon[0], lon[1], lon[2], lonRef);
                            gpsCoordinates = { lat: latitude, lng: longitude };
                        } catch (conversionError) {
                            console.error("Error converting GPS coordinates:", conversionError);
                            // Continue without GPS data if conversion fails
                        }
                    }

                    // Extract relevant EXIF data (e.g., date)
                    const dateTime = EXIF.getTag(this, "DateTimeOriginal") || EXIF.getTag(this, "DateTimeDigitized") || EXIF.getTag(this, "DateTime");

                    resolve({
                        exifData: {
                            dateTime: dateTime
                            // Add other relevant EXIF tags here if needed
                        },
                        gpsCoordinates: gpsCoordinates
                    });
                });
            } catch (error) {
                console.error("Error processing EXIF data:", error);
                // Resolve with no data if EXIF.getData fails
                 resolve({ exifData: null, gpsCoordinates: null, error: error.message });
            }
        });
    },

    // Helper function to convert DMS (Degrees, Minutes, Seconds) to DD (Decimal Degrees)
    convertDMSToDD: function(degrees, minutes, seconds, direction) {
        if (typeof degrees === 'undefined' || typeof minutes === 'undefined' || typeof seconds === 'undefined' || typeof direction === 'undefined') {
            throw new Error("Invalid DMS values for conversion.");
        }
        // Sometimes degrees, minutes, seconds are objects with numerator/denominator
        const deg = (degrees.numerator !== undefined) ? degrees.numerator / degrees.denominator : degrees;
        const min = (minutes.numerator !== undefined) ? minutes.numerator / minutes.denominator : minutes;
        const sec = (seconds.numerator !== undefined) ? seconds.numerator / seconds.denominator : seconds;

        let dd = deg + min / 60 + sec / 3600;

        if (direction === "S" || direction === "W") {
            dd = dd * -1;
        }
        // No conversion needed for N/E
        
        // Basic validation
        if (isNaN(dd)) {
             throw new Error("Could not convert DMS to Decimal Degrees. Result is NaN.");
        }
        if ((direction === "S" || direction === "N") && (dd < -90 || dd > 90)) {
             console.warn(`Calculated latitude ${dd} is outside valid range (-90 to 90).`);
             // Clamp or handle as error? For now, allow it but warn.
             // dd = Math.max(-90, Math.min(90, dd)); 
        }
         if ((direction === "W" || direction === "E") && (dd < -180 || dd > 180)) {
             console.warn(`Calculated longitude ${dd} is outside valid range (-180 to 180).`);
             // Clamp or handle as error? For now, allow it but warn.
             // dd = Math.max(-180, Math.min(180, dd)); 
         }

        return dd;
    }
};

// Make functions available globally
window.extractExifData = extractExifData;
window.extractGpsCoordinates = extractGpsCoordinates;
window.processImageExif = processImageExif; 