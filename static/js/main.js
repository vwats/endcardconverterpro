// Main JavaScript for EndCard Converter Pro

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const combinedUploadForm = document.getElementById('combined-upload-form');
    const portraitFileInput = document.getElementById('portrait-file-input');
    const landscapeFileInput = document.getElementById('landscape-file-input');
    const combinedUploadBtn = document.getElementById('combined-upload-btn');

    const endcardIdField = document.getElementById('endcard-id');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const resultsContainer = document.getElementById('results-container');
    const portraitPreview = document.getElementById('portrait-preview');
    const landscapePreview = document.getElementById('landscape-preview');
    const downloadBothBtn = document.getElementById('download-both');

    // Store HTML content for downloads
    let portraitHTML = '';
    let landscapeHTML = '';
    let portraitFilename = '';
    let landscapeFilename = '';

    // Function to download both versions
    async function downloadBothVersions() {
        try {
            if (portraitHTML && landscapeHTML) {
                const portraitBlob = new Blob([portraitHTML], { type: 'text/html' });
                const landscapeBlob = new Blob([landscapeHTML], { type: 'text/html' });

                const portraitUrl = window.URL.createObjectURL(portraitBlob);
                const landscapeUrl = window.URL.createObjectURL(landscapeBlob);

                // Create and trigger portrait download
                const portraitLink = document.createElement('a');
                portraitLink.href = portraitUrl;
                portraitLink.download = portraitFilename || 'endcard_portrait.html';
                document.body.appendChild(portraitLink);
                portraitLink.click();

                // Small delay between downloads
                await new Promise(resolve => setTimeout(resolve, 100));

                // Create and trigger landscape download
                const landscapeLink = document.createElement('a');
                landscapeLink.href = landscapeUrl;
                landscapeLink.download = landscapeFilename || 'endcard_landscape.html';
                document.body.appendChild(landscapeLink);
                landscapeLink.click();

                // Cleanup
                window.URL.revokeObjectURL(portraitUrl);
                window.URL.revokeObjectURL(landscapeUrl);
                document.body.removeChild(portraitLink);
                document.body.removeChild(landscapeLink);
            }
        } catch (error) {
            console.error('Download failed:', error);
        }
    }

    // Add click event listener for download button
    if (downloadBothBtn) {
        downloadBothBtn.addEventListener('click', downloadBothVersions);
    }
    let currentEndcardId = '';

    // Initialize MRAID and handle events
if (typeof mraid !== 'undefined') {
    if (mraid.getState() === 'loading') {
        mraid.addEventListener('ready', mraidIsReady);
    } else {
        mraidIsReady();
    }
}

function mraidIsReady() {
    mraid.useCustomClose(true);

    // Handle video autoplay if present
    const video = document.querySelector('video');
    if (video) {
        video.play().catch(function(error) {
            console.log("Video autoplay failed:", error);
        });
    }
}

// Check URL parameters for endcard_id (for editing)
window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search);
    const endcardId = urlParams.get('endcard_id');
    if (endcardId) {
        endcardIdField.value = endcardId;
        currentEndcardId = endcardId;
    }
};

    // Handle combined upload form submission
    combinedUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Reset UI state
        hideElement(errorContainer);

        const portraitFile = portraitFileInput.files[0];
        const landscapeFile = landscapeFileInput.files[0];

        // Validate at least one file is selected
        if (!portraitFile && !landscapeFile) {
            showError('Please select at least one file for conversion');
            return;
        }

        const MAX_FILE_SIZE = 2.2 * 1024 * 1024; // 2.2MB per file
        const validTypes = ['image/jpeg', 'image/png', 'video/mp4'];

        // Validate portrait file if provided
        if (portraitFile) {
            // Check file size
            if (portraitFile.size > MAX_FILE_SIZE) {
                showError(`Portrait file size (${(portraitFile.size / (1024 * 1024)).toFixed(2)}MB) exceeds the 2.2MB limit`);
                return;
            }

            // Check file type
            if (!validTypes.includes(portraitFile.type)) {
                showError('Invalid portrait file type. Please upload a JPEG, PNG, or MP4 file');
                return;
            }
        }

        // Validate landscape file if provided
        if (landscapeFile) {
            // Check file size
            if (landscapeFile.size > MAX_FILE_SIZE) {
                showError(`Landscape file size (${(landscapeFile.size / (1024 * 1024)).toFixed(2)}MB) exceeds the 2.2MB limit`);
                return;
            }

            // Check file type
            if (!validTypes.includes(landscapeFile.type)) {
                showError('Invalid landscape file type. Please upload a JPEG, PNG, or MP4 file');
                return;
            }
        }

        // Show loading indicator
        showElement(loadingIndicator);
        disableElement(combinedUploadBtn);

        // Create FormData and append files
        const formData = new FormData();

        if (portraitFile) {
            formData.append('portrait_file', portraitFile);
        }

        if (landscapeFile) {
            formData.append('landscape_file', landscapeFile);
        }

        // Add endcard_id if editing an existing record
        if (endcardIdField.value) {
            formData.append('endcard_id', endcardIdField.value);
        }

        // Send request to server
        fetch('/upload/combined', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error converting files');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            hideElement(loadingIndicator);
            enableElement(combinedUploadBtn);

            // Store endcard ID
            if (data.endcard_id) {
                endcardIdField.value = data.endcard_id;
                currentEndcardId = data.endcard_id;
            }

            // Process portrait data if available
            if (data.portrait) {
                portraitHTML = data.portrait;
                portraitFilename = data.portrait_info.filename;
                updatePreview(portraitPreview, portraitHTML);
            }

            // Process landscape data if available
            if (data.landscape) {
                landscapeHTML = data.landscape;
                landscapeFilename = data.landscape_info.filename;
                updatePreview(landscapePreview, landscapeHTML);
            }

            // Show results and scroll to them
            showElement(resultsContainer);
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        })
        .catch(error => {
            hideElement(loadingIndicator);
            enableElement(combinedUploadBtn);
            showError(error.message);
        });
    });

    // Handle download button
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            if (portraitHTML && portraitFilename) {
                downloadHTML('portrait', portraitFilename, portraitHTML);
            } else {
                showError('No endcard available. Please upload a file first.');
            }
        });
    }

    // Helper Functions
    function showElement(element) {
        if (element) element.classList.remove('d-none');
    }

    function hideElement(element) {
        if (element) element.classList.add('d-none');
    }

    function enableElement(element) {
        if (element) element.disabled = false;
    }

    function disableElement(element) {
        if (element) element.disabled = true;
    }

    function showError(message) {
        if (errorMessage) errorMessage.textContent = message;
        showElement(errorContainer);
    }

    function updatePreview(previewFrame, htmlContent) {
        if (!previewFrame || !htmlContent) return;

        try {
            const container = document.createElement('div');
            container.innerHTML = htmlContent;

            // Set comprehensive sandbox attributes
            previewFrame.setAttribute('sandbox', [
                'allow-scripts',
                'allow-same-origin',
                'allow-modals',
                'allow-forms',
                'allow-popups',
                'allow-popups-to-escape-sandbox',
                'allow-presentation'
            ].join(' '));

            // Create a base HTML wrapper with robust CSP
            const baseHTML = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script>
                    // MRAID Debug Script
                    document.addEventListener('DOMContentLoaded', () => {
                        const testElement = document.createElement('div');
                        testElement.textContent = 'DOM Loaded';
                        testElement.style.cssText = 'color:red; position:fixed; top:10px; left:10px; z-index:9999;';
                        document.body.prepend(testElement);

                        console.assert(window.mraid, 'MRAID Missing!');
                        console.log('MRAID State:', JSON.stringify(window.mraid, null, 2));
                    });

                    // Direct window mutation for MRAID mock
                    window.mraid = {
                        state: 'ready',
                        getState: function() { return this.state; },
                        addEventListener: function(event, callback) {
                            console.debug('[MRAID] Event:', event);
                            if (event === 'ready') {
                                setTimeout(() => {
                                    callback();
                                    console.log('[MRAID] Ready Fired');
                                }, 0);
                            }
                            if (event === 'stateChange') {
                                callback(this.state);
                            }
                            if (event === 'sizeChange') {
                                callback({width: window.innerWidth, height: window.innerHeight});
                            }
                        },
                        removeEventListener: function() {},
                        useCustomClose: function() {},
                        open: function(url) { console.log('[MRAID] Open:', url); },
                        close: function() { console.log('[MRAID] Close called'); },
                        expand: function() { console.log('[MRAID] Expand called'); },
                        getExpandProperties: function() {
                            return {width: window.innerWidth, height: window.innerHeight};
                        }
                    };

                    // Dispatch mraidready event
                    window.addEventListener('DOMContentLoaded', function() {
                        console.log('[MRAID] DOM Ready, dispatching mraidready');
                        window.dispatchEvent(new Event('mraidready'));
                    });
                    // Debug hook for MRAID inspection
                    window.__mraidDebug = () => console.dir(window.mraid);
                    </script>
                </head>
                <body style="margin:0;padding:0;background:#000;">
                    ${htmlContent}
                    <script>
                    // Verify MRAID setup
                    console.log('[DEBUG] MRAID exists:', typeof mraid !== 'undefined');
                    console.log('[DEBUG] MRAID state:', mraid.getState());
                    console.log('[DEBUG] DOM state:', document.readyState);
                    </script>
                </body>
                </html>`;

            // Set up preview frame with all necessary permissions
            previewFrame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-popups allow-presentation allow-forms allow-modals');

            // Create blob URL with error handling
            try {
                const blob = new Blob([baseHTML], {type: 'text/html;charset=utf-8'});
                const blobUrl = URL.createObjectURL(blob);

                previewFrame.onload = () => {
                    try {
                        console.log('[Preview] Frame loaded');
                        // Direct MRAID injection fallback
                        const frameWindow = previewFrame.contentWindow;
                        if (frameWindow && typeof frameWindow.mraid === 'undefined') {
                            console.log('[Preview] Fallback MRAID injection');
                            Object.defineProperty(frameWindow, 'mraid', {
                                value: window.mraid,
                                writable: false,
                                configurable: false
                            });
                        }
                        URL.revokeObjectURL(blobUrl);
                    } catch (loadError) {
                        console.error('[Preview] Frame load error:', loadError);
                    }
                };

                previewFrame.onerror = (error) => {
                    console.error('[Preview] Frame error:', error);
                };

                previewFrame.src = blobUrl;
            } catch (blobError) {
                console.error('[Preview] Blob creation error:', blobError);
            }
        } catch (error) {
            console.error("Preview update failed:", error);
        }
    }

    // Add rotation toggle functionality
    const rotateBtn = document.getElementById('rotate-btn');
    if (rotateBtn) {
        rotateBtn.addEventListener('click', function() {
            const previewFrames = [portraitPreview, landscapePreview];
            previewFrames.forEach(frame => {
                if (frame) {
                    frame.classList.toggle('rotated');
                    updatePreview(frame, frame === portraitPreview ? portraitHTML : landscapeHTML);
                }
            });
        });
    }

    function downloadHTML(orientation, filename, htmlContent) {
        if (!filename || !htmlContent) return;

        const baseFilename = filename.split('.')[0];
        const blob = new Blob([htmlContent], {type: 'text/html;charset=utf-8'});
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${baseFilename}_${orientation}.html`;
        document.body.appendChild(link);
        link.click();
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(link);
        }, 100);
    }
});