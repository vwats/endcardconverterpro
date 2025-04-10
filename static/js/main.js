// Main JavaScript for EndCard Converter Pro

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const combinedUploadForm = document.getElementById('combined-upload-form');
    const mediaFileInput = document.getElementById('media-file-input');
    const combinedUploadBtn = document.getElementById('combined-upload-btn');
    const clearFileBtn = document.getElementById('clear-file-btn');
    const previewArea = document.querySelector('.preview-area');
    const mediaPreview = document.getElementById('media-preview');
    const videoPreview = document.getElementById('video-preview');

    // Results and preview elements
    const endcardIdField = document.getElementById('endcard-id');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const resultsContainer = document.getElementById('results-container');
    const endcardPreview = document.getElementById('endcard-preview');
    const previewContainer = document.getElementById('preview-container');
    const orientationStatus = document.getElementById('orientation-status');
    const rotatePreviewBtn = document.getElementById('rotate-preview-btn');
    const downloadEndcardBtn = document.getElementById('download-endcard-btn');

    // State variables
    let currentOrientation = 'portrait'; // 'portrait' or 'landscape'
    let htmlContent = '';
    let uploadedFilename = '';
    let currentEndcardId = '';

    // File input change handler
    mediaFileInput.addEventListener('change', function(e) {
        const file = mediaFileInput.files[0];
        if (!file) {
            return;
        }

        // Preview the file
        const isVideo = file.type.startsWith('video/');
        const fileURL = URL.createObjectURL(file);
        
        if (isVideo) {
            // Set video source and show video preview
            videoPreview.src = fileURL;
            showElement(videoPreview);
            hideElement(mediaPreview);
        } else {
            // Set image source and show image preview
            mediaPreview.src = fileURL;
            showElement(mediaPreview);
            hideElement(videoPreview);
        }
        
        // Show preview area and enable generate button
        showElement(previewArea);
        enableElement(combinedUploadBtn);
    });

    // Clear file button handler
    clearFileBtn.addEventListener('click', function() {
        mediaFileInput.value = '';
        hideElement(previewArea);
        disableElement(combinedUploadBtn);
    });

    // Rotate preview button handler
    rotatePreviewBtn.addEventListener('click', function() {
        toggleOrientation();
    });

    // Download endcard button handler
    downloadEndcardBtn.addEventListener('click', function() {
        if (htmlContent && uploadedFilename) {
            downloadHTML('rotatable', uploadedFilename, htmlContent);
        } else {
            showError('No endcard available. Please upload a file and generate an endcard first.');
        }
    });

    // Toggle orientation function
    function toggleOrientation() {
        if (currentOrientation === 'portrait') {
            currentOrientation = 'landscape';
            previewContainer.classList.remove('portrait-container');
            previewContainer.classList.add('landscape-container');
            orientationStatus.textContent = 'Landscape Mode';
        } else {
            currentOrientation = 'portrait';
            previewContainer.classList.remove('landscape-container');
            previewContainer.classList.add('portrait-container');
            orientationStatus.textContent = 'Portrait Mode';
        }
    }

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

    // Form submission handler
    combinedUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Reset UI state
        hideElement(errorContainer);

        const mediaFile = mediaFileInput.files[0];

        // Validate file is selected
        if (!mediaFile) {
            showError('Please select a file for conversion');
            return;
        }

        const MAX_FILE_SIZE = 2.2 * 1024 * 1024; // 2.2MB
        const validTypes = ['image/jpeg', 'image/png', 'video/mp4'];

        // Check file size
        if (mediaFile.size > MAX_FILE_SIZE) {
            showError(`File size (${(mediaFile.size / (1024 * 1024)).toFixed(2)}MB) exceeds the 2.2MB limit`);
            return;
        }

        // Check file type
        if (!validTypes.includes(mediaFile.type)) {
            showError('Invalid file type. Please upload a JPEG, PNG, or MP4 file');
            return;
        }

        // Show loading indicator
        showElement(loadingIndicator);
        disableElement(combinedUploadBtn);

        // Create FormData and append file
        const formData = new FormData();
        formData.append('media_file', mediaFile);

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
                    throw new Error(data.error || 'Error converting file');
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

            // Store HTML content and filename
            htmlContent = data.html;
            uploadedFilename = data.file_info.filename;

            // Update preview
            updatePreview(endcardPreview, htmlContent);

            // Reset orientation to portrait
            currentOrientation = 'portrait';
            previewContainer.classList.remove('landscape-container');
            previewContainer.classList.add('portrait-container');
            orientationStatus.textContent = 'Portrait Mode';

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
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
        const blob = new Blob([htmlContent], {type: 'text/html;charset=utf-8'});
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        if (orientation === 'rotatable') {
            link.download = `${baseFilename}_endcard.html`;
        } else {
            link.download = `${baseFilename}_${orientation}.html`;
        }
        
        document.body.appendChild(link);
        link.click();
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
            document.body.removeChild(link);
        }, 100);
    }
});