// Main JavaScript for EndCard Converter Pro

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
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
    let originalFilename = '';

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Reset UI state
        hideElement(errorContainer);
        hideElement(resultsContainer);
        
        const file = fileInput.files[0];
        
        // Validate file selection
        if (!file) {
            showError('Please select a file to upload');
            return;
        }
        
        // Validate file size (2.2MB max)
        if (file.size > 2.2 * 1024 * 1024) {
            showError('File size exceeds the 2.2MB limit');
            return;
        }
        
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'video/mp4'];
        if (!validTypes.includes(file.type)) {
            showError('Invalid file type. Please upload a JPEG, PNG, or MP4 file');
            return;
        }
        
        // Show loading indicator
        showElement(loadingIndicator);
        disableElement(uploadBtn);
        
        // Create FormData and append file
        const formData = new FormData();
        formData.append('file', file);
        
        // Send request to server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Error uploading file');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            hideElement(loadingIndicator);
            enableElement(uploadBtn);
            
            // Store HTML content for downloads
            portraitHTML = data.portrait;
            landscapeHTML = data.landscape;
            originalFilename = data.filename;
            
            // Update previews
            updatePreview(portraitPreview, portraitHTML);
            updatePreview(landscapePreview, landscapeHTML);
            
            // Show results
            showElement(resultsContainer);
        })
        .catch(error => {
            hideElement(loadingIndicator);
            enableElement(uploadBtn);
            showError(error.message);
        });
    });

    // Handle download buttons
    downloadPortraitBtn.addEventListener('click', function() {
        if (portraitHTML) {
            downloadHTML('portrait', originalFilename, portraitHTML);
        }
    });

    downloadLandscapeBtn.addEventListener('click', function() {
        if (landscapeHTML) {
            downloadHTML('landscape', originalFilename, landscapeHTML);
        }
    });

    // Helper Functions
    function showElement(element) {
        element.classList.remove('d-none');
    }

    function hideElement(element) {
        element.classList.add('d-none');
    }

    function enableElement(element) {
        element.disabled = false;
    }

    function disableElement(element) {
        element.disabled = true;
    }

    function showError(message) {
        errorMessage.textContent = message;
        showElement(errorContainer);
    }

    function updatePreview(iframeElement, htmlContent) {
        // Update the iframe content
        const iframe = iframeElement;
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        
        iframeDoc.open();
        iframeDoc.write(htmlContent);
        iframeDoc.close();
    }

    function downloadHTML(orientation, filename, htmlContent) {
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
