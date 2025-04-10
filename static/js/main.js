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
    const downloadPortraitBtn = document.getElementById('download-portrait');
    const downloadLandscapeBtn = document.getElementById('download-landscape');

    // Store HTML content for downloads
    let portraitHTML = '';
    let landscapeHTML = '';
    let portraitFilename = '';
    let landscapeFilename = '';
    let currentEndcardId = '';

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

    // Handle download buttons
    downloadPortraitBtn.addEventListener('click', function() {
        if (portraitHTML && portraitFilename) {
            downloadHTML('portrait', portraitFilename, portraitHTML);
        } else {
            showError('No portrait endcard available. Please upload a portrait file first.');
        }
    });

    downloadLandscapeBtn.addEventListener('click', function() {
        if (landscapeHTML && landscapeFilename) {
            downloadHTML('landscape', landscapeFilename, landscapeHTML);
        } else {
            showError('No landscape endcard available. Please upload a landscape file first.');
        }
    });

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

    function updatePreview(iframeElement, htmlContent) {
        if (!iframeElement || !htmlContent) return;

        // Update the iframe content
        const iframe = iframeElement;
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

        iframeDoc.open();
        iframeDoc.write(htmlContent);
        iframeDoc.close();
    }

    function downloadHTML(orientation, filename, htmlContent) {
        if (!filename || !htmlContent) return;

        const baseFilename = filename.split('.')[0];

        fetch(`/download/${orientation}/${filename}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html'
            },
            body: new URLSearchParams({
                html: htmlContent
            }).toString()
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Download failed');
                });
            }
            return response.blob();
        })
        .then(blob => {
            if (blob.type !== 'text/html') {
                const newBlob = new Blob([blob], {type: 'text/html'});
                return newBlob;
            }
            return blob;
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${baseFilename}_${orientation}.html`;
            document.body.appendChild(link);
            link.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(link);
        })
        .catch(error => {
            console.error('Download failed:', error);
            showError('Failed to download the file. Please try again.');
        });
    }
});