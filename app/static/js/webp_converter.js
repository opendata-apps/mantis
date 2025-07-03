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

            const originalFileName = file.name || file.originalFileName || 'unknown.jpg';
            let fileToProcess = file;
            let wasHeic = false;

            // Quick size check to prevent memory issues
            const maxFileSize = 50 * 1024 * 1024; // 50MB limit for processing
            if (file.size > maxFileSize) {
                return reject(new Error(`File too large for processing: ${(file.size / 1024 / 1024).toFixed(1)}MB. Maximum: 50MB`));
            }

            // --- HEIC/HEIF Conversion (if necessary) ---
            // Check if file is actually HEIC/HEIF by MIME type (not just filename)
            const isActuallyHeic = file.type === 'image/heic' || file.type === 'image/heif';
            
            if (isActuallyHeic) {
                if (typeof heic2any !== 'function') {
                    console.error('heic2any library not loaded.');
                    return reject(new Error('HEIC conversion library not loaded.'));
                }
                try {
                    const conversionResult = await heic2any({ 
                        blob: file,
                        toType: "image/jpeg",
                        quality: 0.85
                    });
                    fileToProcess = conversionResult;
                    wasHeic = true;
                } catch (heicError) {
                    console.error('Error converting HEIC/HEIF:', heicError);
                    return reject(new Error(`HEIC/HEIF conversion failed: ${heicError.message || heicError}`));
                }
            }

            // --- WebP Conversion using Canvas with size optimization ---
            const loadImageAndConvertToWebp = (imageSource) => {
                const img = new Image();
                
                img.onload = () => {
                    try {
                        let objectUrlCreated = imageSource.startsWith('blob:');
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        
                        // Calculate optimal dimensions to prevent memory issues
                        // Use smaller dimensions on mobile devices to prevent memory crashes
                        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                        const maxDimension = isMobile ? 2048 : 4096; // Smaller limit for mobile
                        let { width, height } = WebpConverter.calculateOptimalDimensions(
                            img.naturalWidth, 
                            img.naturalHeight, 
                            maxDimension
                        );
                        
                        try {
                            canvas.width = width;
                            canvas.height = height;
                            
                            // Draw image with potential resizing
                            ctx.drawImage(img, 0, 0, width, height);
                        } catch (canvasError) {
                            console.error('Canvas operation failed, trying with smaller dimensions:', canvasError);
                            // If canvas operations fail (likely due to memory), try with even smaller dimensions
                            const fallbackDimension = isMobile ? 1024 : 2048;
                            const fallback = WebpConverter.calculateOptimalDimensions(
                                img.naturalWidth, 
                                img.naturalHeight, 
                                fallbackDimension
                            );
                            width = fallback.width;
                            height = fallback.height;
                            canvas.width = width;
                            canvas.height = height;
                            ctx.drawImage(img, 0, 0, width, height);
                        }
                        
                        // Revoke Object URL if one was created
                        if (objectUrlCreated) { 
                            URL.revokeObjectURL(img.src); 
                        }

                        // Convert canvas to WebP Blob with quality based on file size
                        const quality = WebpConverter.calculateOptimalQuality(file.size, width, height);
                        
                        canvas.toBlob((blob) => {
                            if (!blob) {
                                return reject(new Error('Canvas to WebP Blob conversion failed.'));
                            }
                            
                            // Create a data URL for preview purposes
                            const dataUrl = canvas.toDataURL('image/webp', quality);
                            
                            console.log(`WebP conversion complete: ${(blob.size / 1024).toFixed(1)}KB (quality: ${quality})`);
                            
                            resolve({
                                blob: blob,
                                dataUrl: dataUrl,
                                originalFileName: originalFileName
                            });

                        }, 'image/webp', quality);
                        
                    } catch (toBlobError) {
                        console.error("Error during canvas processing:", toBlobError);
                        reject(new Error(`Failed to convert canvas to WebP: ${toBlobError.message}`));
                    }
                };
                
                img.onerror = (error) => {
                    let objectUrlCreated = imageSource.startsWith('blob:');
                    if (objectUrlCreated) { 
                        URL.revokeObjectURL(img.src); 
                    }
                    console.error("Error loading image for WebP conversion:", error);
                    reject(new Error('Could not load image data for conversion.'));
                };

                img.src = imageSource;
            };

            // --- Trigger Image Loading ---
            if (wasHeic) {
                const objectUrl = URL.createObjectURL(fileToProcess);
                loadImageAndConvertToWebp(objectUrl);
            } else {
                const reader = new FileReader();
                reader.onload = (event) => {
                    loadImageAndConvertToWebp(event.target.result); 
                };
                reader.onerror = (error) => {
                    console.error("FileReader error:", error);
                    reject(new Error('Error reading file.'));
                };
                reader.readAsDataURL(fileToProcess);
            }
        });
    },

    // Calculate optimal dimensions to prevent memory issues
    calculateOptimalDimensions: function(originalWidth, originalHeight, maxDimension) {
        if (originalWidth <= maxDimension && originalHeight <= maxDimension) {
            return { width: originalWidth, height: originalHeight };
        }
        
        const aspectRatio = originalWidth / originalHeight;
        
        if (originalWidth > originalHeight) {
            return {
                width: maxDimension,
                height: Math.round(maxDimension / aspectRatio)
            };
        } else {
            return {
                width: Math.round(maxDimension * aspectRatio),
                height: maxDimension
            };
        }
    },

    // Calculate optimal quality based on file size and dimensions
    calculateOptimalQuality: function(fileSize, width, height) {
        const pixels = width * height;
        const fileSizeMB = fileSize / (1024 * 1024);
        
        // Start with base quality
        let quality = 0.8;
        
        // Reduce quality for large files
        if (fileSizeMB > 10) {
            quality = 0.6;
        } else if (fileSizeMB > 5) {
            quality = 0.7;
        }
        
        // Reduce quality for high-resolution images
        if (pixels > 8000000) { // > 8MP
            quality = Math.min(quality, 0.6);
        } else if (pixels > 4000000) { // > 4MP
            quality = Math.min(quality, 0.7);
        }
        
        return Math.max(0.5, quality); // Never go below 0.5 quality
    }
};