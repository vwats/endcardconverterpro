// Main JavaScript for EndCard Converter Pro

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const combinedUploadForm = document.getElementById('combined-upload-form');
    const portraitFileInput = document.getElementById('portrait-file-input');
    const landscapeFileInput = document.getElementById('landscape-file-input');
    const combinedUploadBtn = document.getElementById('combined-upload-btn');
    const clearFileBtn = document.getElementById('clear-file-btn');
    const previewArea = document.querySelector('.preview-area');
    const mediaPreview = document.getElementById('media-preview');
    const videoPreview = document.getElementById('video-preview');
    const endcardPreview = document.getElementById('endcard-preview');
    const previewContainer = document.getElementById('preview-container');
    const orientationStatus = document.getElementById('orientation-status');
    const rotatePreviewBtn = document.getElementById('rotate-preview-btn');
    const downloadEndcardBtn = document.getElementById('download-endcard-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const resultsContainer = document.getElementById('results-container');
    const endcardIdField = document.getElementById('endcard-id');

    // State variables
    let currentOrientation = 'portrait';
    let portraitHtml = '';
    let landscapeHtml = '';
    let uploadedFilename = '';
    let currentEndcardId = '';

    // File input change handlers
    [portraitFileInput, landscapeFileInput].forEach(input => {
        input.addEventListener('change', function(e) {
            const file = this.files[0];
            if (!file) return;

            if (this === portraitFileInput) {
                const isVideo = file.type.startsWith('video/');
                const fileURL = URL.createObjectURL(file);

                if (isVideo) {
                    videoPreview.src = fileURL;
                    showElement(videoPreview);
                    hideElement(mediaPreview);
                } else {
                    mediaPreview.src = fileURL;
                    showElement(mediaPreview);
                    hideElement(videoPreview);
                }

                showElement(previewArea);
            }

            if (portraitFileInput.files[0] && landscapeFileInput.files[0]) {
                enableElement(combinedUploadBtn);
            } else {
                disableElement(combinedUploadBtn);
            }
        });
    });

    // Clear file button handler
    if (clearFileBtn) {
        clearFileBtn.addEventListener('click', function() {
            portraitFileInput.value = '';
            landscapeFileInput.value = '';
            hideElement(previewArea);
            disableElement(combinedUploadBtn);
        });
    }

    // Rotate preview button handler
    if (rotatePreviewBtn) {
        rotatePreviewBtn.addEventListener('click', toggleOrientation);
    }

    // Download endcard button handler
    if (downloadEndcardBtn) {
        downloadEndcardBtn.addEventListener('click', function() {
            if (!portraitHtml || !landscapeHtml || !uploadedFilename) {
                showError('No endcard available. Please upload files and generate an endcard first.');
                return;
            }

            const htmlContent = currentOrientation === 'portrait' ? portraitHtml : landscapeHtml;
            downloadHTML(currentOrientation, uploadedFilename, htmlContent);
        });
    }

    // Store URLs for both orientations
    let portraitURL = '';
    let landscapeURL = '';
    let portraitIsVideo = false;
    let landscapeIsVideo = false;

    // Toggle orientation function
    function toggleOrientation() {
        if (!previewContainer || !orientationStatus) return;

        currentOrientation = currentOrientation === 'portrait' ? 'landscape' : 'portrait';

        // Update container classes
        previewContainer.classList.remove('portrait-container', 'landscape-container');
        previewContainer.classList.add(`${currentOrientation}-container`);

        // Update status text
        orientationStatus.textContent = `${currentOrientation.charAt(0).toUpperCase() + currentOrientation.slice(1)} Mode`;

        // Switch between stored URLs
        if (currentOrientation === 'portrait') {
            if (portraitIsVideo) {
                videoPreview.src = portraitURL;
                videoPreview.style.display = 'block';
                mediaPreview.style.display = 'none';
            } else {
                mediaPreview.src = portraitURL;
                mediaPreview.style.display = 'block';
                videoPreview.style.display = 'none';
            }
        } else {
            if (landscapeIsVideo) {
                videoPreview.src = landscapeURL;
                videoPreview.style.display = 'block';
                mediaPreview.style.display = 'none';
            } else {
                mediaPreview.src = landscapeURL;
                mediaPreview.style.display = 'block';
                videoPreview.style.display = 'none';
            }
        }

        // Update HTML content
        const htmlContent = currentOrientation === 'portrait' ? portraitHtml : landscapeHtml;
        if (endcardPreview) {
            updatePreview(endcardPreview, htmlContent);
        }
    }

    // Update file input change handlers
    [portraitFileInput, landscapeFileInput].forEach(input => {
        input.addEventListener('change', function(e) {
            const file = this.files[0];
            if (!file) return;

            const isVideo = file.type.startsWith('video/');
            const fileURL = URL.createObjectURL(file);

            if (this === portraitFileInput) {
                if (portraitURL) URL.revokeObjectURL(portraitURL);
                portraitURL = fileURL;
                portraitIsVideo = isVideo;
            } else {
                if (landscapeURL) URL.revokeObjectURL(landscapeURL);
                landscapeURL = fileURL;
                landscapeIsVideo = isVideo;
            }

            // Update current preview
            if ((this === portraitFileInput && currentOrientation === 'portrait') ||
                (this === landscapeFileInput && currentOrientation === 'landscape')) {
                if (isVideo) {
                    videoPreview.src = fileURL;
                    videoPreview.style.display = 'block';
                    mediaPreview.style.display = 'none';
                } else {
                    mediaPreview.src = fileURL;
                    mediaPreview.style.display = 'block';
                    videoPreview.style.display = 'none';
                }
            }

            showElement(previewArea);

            if (portraitFileInput.files[0] && landscapeFileInput.files[0]) {
                enableElement(combinedUploadBtn);
            } else {
                disableElement(combinedUploadBtn);
            }
        });
    });

    // Form submission handler
    combinedUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        hideElement(errorContainer);

        const portraitFile = portraitFileInput.files[0];
        const landscapeFile = landscapeFileInput.files[0];

        if (!portraitFile || !landscapeFile) {
            showError('Please select both portrait and landscape files');
            return;
        }

        const MAX_FILE_SIZE = 2.2 * 1024 * 1024;
        const validTypes = ['image/jpeg', 'image/png', 'video/mp4'];

        if (portraitFile.size > MAX_FILE_SIZE || landscapeFile.size > MAX_FILE_SIZE) {
            showError('File size exceeds the 2.2MB limit');
            return;
        }

        if (!validTypes.includes(portraitFile.type) || !validTypes.includes(landscapeFile.type)) {
            showError('Invalid file type. Please upload JPEG, PNG, or MP4 files');
            return;
        }

        showElement(loadingIndicator);
        disableElement(combinedUploadBtn);

        const formData = new FormData();
        formData.append('portrait_file', portraitFile);
        formData.append('landscape_file', landscapeFile);

        if (endcardIdField.value) {
            formData.append('endcard_id', endcardIdField.value);
        }

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
            hideElement(loadingIndicator);
            enableElement(combinedUploadBtn);

            if (data.endcard_id) {
                endcardIdField.value = data.endcard_id;
                currentEndcardId = data.endcard_id;
            }

            portraitHtml = data.portrait;
            landscapeHtml = data.landscape;
            uploadedFilename = data.portrait_info.filename;

            currentOrientation = 'portrait';
            updatePreview(endcardPreview, portraitHtml);

            previewContainer.classList.remove('landscape-container');
            previewContainer.classList.add('portrait-container');
            orientationStatus.textContent = 'Portrait Mode';

            showElement(resultsContainer);
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        })
        .catch(error => {
            hideElement(loadingIndicator);
            enableElement(combinedUploadBtn);
            showError(error.message);
        });
    });

    function downloadHTML(orientation, filename, htmlContent) {
        if (!filename || !htmlContent) return;

        const baseFilename = filename.split('.')[0];
        const outputFilename = `${baseFilename}_${orientation}.html`;

        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');

        link.href = url;
        link.download = outputFilename;
        document.body.appendChild(link);

        link.click();

        setTimeout(() => {
            URL.revokeObjectURL(url);
            document.body.removeChild(link);
        }, 100);
    }

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

        const iframe = iframeElement;
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

        iframeDoc.open();
        iframeDoc.write(htmlContent);
        iframeDoc.close();
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
});