/**
 * WebP Image Converter for Mantis Religiosa Sighting Form
 * This script handles conversion of various image formats to WebP
 * for efficient upload and storage.
 */

// Function to convert various image formats (including HEIC via heic2any)
// to a WebP Blob and Data URL.

const WebpConverter = {
    processImage: async function(file) {
        return new Promise(async (resolve, reject) => {
            if (!file) {
                return reject(new Error("No file provided."));
            }

            const originalFileName = file.name;
            let fileToProcess = file;
            let wasHeic = false;

            // --- HEIC/HEIF Conversion (if necessary) ---
            const isHeic = file.type === 'image/heic' || file.type === 'image/heif' || 
                         originalFileName.toLowerCase().endsWith('.heic') || originalFileName.toLowerCase().endsWith('.heif');

            if (isHeic) {
                if (typeof heic2any !== 'function') {
                    console.error('heic2any library not loaded.');
                    return reject(new Error('HEIC conversion library not loaded.'));
                }
                try {
                    console.log("Starting HEIC conversion...");
                    // Convert HEIC to JPEG first, as canvas might not handle HEIC directly
                    const conversionResult = await heic2any({ 
                        blob: file,
                        toType: "image/jpeg", // Convert HEIC to JPEG temporarily
                        quality: 0.85 // Keep JPEG quality reasonable
                    });
                    fileToProcess = conversionResult; // Use the converted JPEG blob
                    wasHeic = true;
                    console.log("HEIC converted successfully to JPEG for processing.");
                } catch (heicError) {
                    console.error('Error converting HEIC/HEIF:', heicError);
                    return reject(new Error(`HEIC/HEIF conversion failed: ${heicError.message || heicError}`));
                }
            }

            // --- WebP Conversion using Canvas --- 

            // Define image loading and conversion logic (used by both paths)
            const loadImageAndConvertToWebp = (imageSource) => {
                const img = new Image();
                
                img.onload = () => {
                    let objectUrlCreated = imageSource.startsWith('blob:'); // Track if we need to revoke
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = img.naturalWidth; // Use natural dimensions
                    canvas.height = img.naturalHeight;
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    
                    // Revoke Object URL if one was created for this image loading step
                    if (objectUrlCreated) { 
                        URL.revokeObjectURL(img.src); 
                    }

                    // Convert canvas to WebP Blob
                    try {
                         canvas.toBlob((blob) => {
                             if (!blob) {
                                 // If blob creation fails, reject the promise
                                 return reject(new Error('Canvas to WebP Blob conversion failed.'));
                             }
                             // Create a data URL for preview purposes
                             const dataUrl = canvas.toDataURL('image/webp', 0.8);
                             
                             resolve({
                                 blob: blob,          // The WebP Blob for uploading
                                 dataUrl: dataUrl,    // The WebP data URL for preview
                                 originalFileName: originalFileName // Keep original name
                             });

                         }, 'image/webp', 0.8); // Quality set to 0.8
                    } catch (toBlobError) {
                         console.error("Error during canvas.toBlob:", toBlobError);
                         // If toBlob throws an error, reject the promise
                         reject(new Error(`Failed to convert canvas to WebP: ${toBlobError.message}`));
                    }
                };
                
                img.onerror = (error) => {
                     let objectUrlCreated = imageSource.startsWith('blob:');
                     // Revoke Object URL if one was created and loading failed
                    if (objectUrlCreated) { 
                        URL.revokeObjectURL(img.src); 
                    }
                    console.error("Error loading image for WebP conversion:", img.src, error);
                    reject(new Error('Could not load image data for conversion.'));
                };

                img.src = imageSource; // Set the source (Data URL or Object URL)
            };

            // --- Trigger Image Loading ---
            if (wasHeic) {
                // If it was HEIC, fileToProcess is a Blob. Use Object URL.
                const objectUrl = URL.createObjectURL(fileToProcess);
                loadImageAndConvertToWebp(objectUrl);
            } else {
                // If it wasn't HEIC, fileToProcess is the original File. Use FileReader.
                const reader = new FileReader();
                reader.onload = (event) => {
                    // Use the Data URL from the FileReader result
                    loadImageAndConvertToWebp(event.target.result); 
                };
                reader.onerror = (error) => {
                    console.error("FileReader error:", error);
                    reject(new Error('Error reading file.'));
                };
                reader.readAsDataURL(fileToProcess);
            }
        });
    }
};