// Main JavaScript for EndCard Converter Pro

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const portraitUploadForm = document.getElementById('portrait-upload-form');
    const portraitFileInput = document.getElementById('portrait-file-input');
    const portraitUploadBtn = document.getElementById('portrait-upload-btn');
    
    const landscapeUploadForm = document.getElementById('landscape-upload-form');
    const landscapeFileInput = document.getElementById('landscape-file-input');
    const landscapeUploadBtn = document.getElementById('landscape-upload-btn');
    
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

    // Handle portrait upload form submission
    portraitUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Reset UI state for portrait
        hideElement(errorContainer);
        
        const file = portraitFileInput.files[0];
        
        // Validate file selection
        if (!file) {
            showError('Please select a file for portrait orientation');
            return;
        }
        
        // Validate file size (2.2MB max)
        if (file.size > 2.2 * 1024 * 1024) {
            showError('Portrait file size exceeds the 2.2MB limit');
            return;
        }
        
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'video/mp4'];
        if (!validTypes.includes(file.type)) {
            showError('Invalid portrait file type. Please upload a JPEG, PNG, or MP4 file');
            return;
        }
        
        // Show loading indicator
        showElement(loadingIndicator);
        disableElement(portraitUploadBtn);
        disableElement(landscapeUploadBtn);
        
        // Create FormData and append file
        const formData = new FormData();
        formData.append('file', file);
        
        // Add endcard_id if editing an existing record
        if (endcardIdField.value) {
            formData.append('endcard_id', endcardIdField.value);
        }
        
        // Send request to server
        fetch('/upload/portrait', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error uploading portrait file');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            hideElement(loadingIndicator);
            enableElement(portraitUploadBtn);
            enableElement(landscapeUploadBtn);
            
            // Store HTML content for downloads
            portraitHTML = data.portrait;
            portraitFilename = data.filename;
            
            // Store endcard ID
            if (data.endcard_id) {
                endcardIdField.value = data.endcard_id;
                currentEndcardId = data.endcard_id;
            }
            
            // Update preview
            updatePreview(portraitPreview, portraitHTML);
            
            // Show results
            showElement(resultsContainer);
        })
        .catch(error => {
            hideElement(loadingIndicator);
            enableElement(portraitUploadBtn);
            enableElement(landscapeUploadBtn);
            showError(error.message);
        });
    });

    // Handle landscape upload form submission
    landscapeUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Reset UI state for landscape
        hideElement(errorContainer);
        
        const file = landscapeFileInput.files[0];
        
        // Validate file selection
        if (!file) {
            showError('Please select a file for landscape orientation');
            return;
        }
        
        // Validate file size (2.2MB max)
        if (file.size > 2.2 * 1024 * 1024) {
            showError('Landscape file size exceeds the 2.2MB limit');
            return;
        }
        
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'video/mp4'];
        if (!validTypes.includes(file.type)) {
            showError('Invalid landscape file type. Please upload a JPEG, PNG, or MP4 file');
            return;
        }
        
        // Show loading indicator
        showElement(loadingIndicator);
        disableElement(portraitUploadBtn);
        disableElement(landscapeUploadBtn);
        
        // Create FormData and append file
        const formData = new FormData();
        formData.append('file', file);
        
        // Add endcard_id if editing an existing record
        if (endcardIdField.value) {
            formData.append('endcard_id', endcardIdField.value);
        }
        
        // Send request to server
        fetch('/upload/landscape', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error uploading landscape file');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            hideElement(loadingIndicator);
            enableElement(portraitUploadBtn);
            enableElement(landscapeUploadBtn);
            
            // Store HTML content for downloads
            landscapeHTML = data.landscape;
            landscapeFilename = data.filename;
            
            // Store endcard ID
            if (data.endcard_id) {
                endcardIdField.value = data.endcard_id;
                currentEndcardId = data.endcard_id;
            }
            
            // Update preview
            updatePreview(landscapePreview, landscapeHTML);
            
            // Show results
            showElement(resultsContainer);
        })
        .catch(error => {
            hideElement(loadingIndicator);
            enableElement(portraitUploadBtn);
            enableElement(landscapeUploadBtn);
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
        
        // Create the download URL with the HTML content
        const baseFilename = filename.split('.')[0];
        const downloadUrl = `/download/${orientation}/${filename}?html=${encodeURIComponent(htmlContent)}`;
        
        // Create a temporary link and trigger the download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `${baseFilename}_${orientation}.html`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});
