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
    let portraitFile = null;
    let landscapeFile = null;
    let currentEndcardId = '';
    let currentData = null;

    // Helper functions
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

    // File input change handlers
    [portraitFileInput, landscapeFileInput].forEach(input => {
        input.addEventListener('change', function(e) {
            const file = this.files[0];
            if (!file) return;

            if (this === portraitFileInput) {
                portraitFile = file;
            } else {
                landscapeFile = file;
            }

            if (portraitFile && landscapeFile) {
                enableElement(combinedUploadBtn);
            }
            updatePreview();
        });
    });

    function updatePreview() {
        const file = currentOrientation === 'portrait' ? portraitFile : landscapeFile;
        if (!file) return;

        const isVideo = file.type.startsWith('video/');
        const fileURL = URL.createObjectURL(file);

        if (isVideo) {
            if (videoPreview) {
                videoPreview.src = fileURL;
                videoPreview.style.display = 'block';
                if (mediaPreview) mediaPreview.style.display = 'none';
            }
        } else {
            if (mediaPreview) {
                mediaPreview.src = fileURL;
                mediaPreview.style.display = 'block';
                if (videoPreview) videoPreview.style.display = 'none';
            }
        }
        showElement(previewArea);
    }

    // Form submission handler
    if (combinedUploadForm) {
        combinedUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!portraitFile || !landscapeFile) {
                showError('Please select both portrait and landscape files.');
                return;
            }

            disableElement(combinedUploadBtn);
            showElement(loadingIndicator);
            hideElement(errorContainer);

            const formData = new FormData();
            formData.append('portrait_file', portraitFile);
            formData.append('landscape_file', landscapeFile);

            if (endcardIdField.value) {
                formData.append('endcard_id', endcardIdField.value);
            }

            fetch('/create-checkout-session', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                    'Origin': window.location.origin
                },
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.error || `HTTP error! status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.id) {
                    throw new Error('Invalid response from server - missing session ID');
                }
                return stripe.redirectToCheckout({ sessionId: data.id }).catch(err => {
                    throw new Error(`Stripe checkout error: ${err.message}`);
                });
            })
            .catch(error => {
                console.error('Payment setup failed:', error);
                alert(`Payment setup failed: ${error.message}`);
                enableElement(combinedUploadBtn);
            });
        });
    }

    function handleUploadSuccess(data) {
        hideElement(loadingIndicator);
        enableElement(combinedUploadBtn);

        if (data.error) {
            throw new Error(data.error);
        }

        currentData = data;

        if (data.endcard_id) {
            endcardIdField.value = data.endcard_id;
            currentEndcardId = data.endcard_id;
        }

        updateEndcardPreview();
        showElement(resultsContainer);
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function handleUploadError(error) {
        hideElement(loadingIndicator);
        enableElement(combinedUploadBtn);
        showError(error.message || 'An error occurred during upload.');
    }

    // Orientation and preview handling
    if (rotatePreviewBtn) {
        rotatePreviewBtn.addEventListener('click', function() {
            currentOrientation = currentOrientation === 'portrait' ? 'landscape' : 'portrait';
            previewContainer.className = `preview-container ${currentOrientation}-container`;
            orientationStatus.textContent = `${currentOrientation.charAt(0).toUpperCase() + currentOrientation.slice(1)} Mode`;
            updatePreview();
            updateEndcardPreview();
        });
    }

    function updateEndcardPreview() {
        if (!endcardPreview || !currentData) return;

        const doc = endcardPreview.contentDocument || endcardPreview.contentWindow.document;
        const htmlContent = currentOrientation === 'portrait' ? currentData.portrait : currentData.landscape;

        // Save current scroll position
        const scrollPos = doc.documentElement ? doc.documentElement.scrollTop : 0;

        doc.open();
        doc.write(htmlContent);
        doc.close();

        // Restore scroll position
        if (doc.documentElement) {
            doc.documentElement.scrollTop = scrollPos;
        }

        // Update orientation status text
        if (orientationStatus) {
            orientationStatus.textContent = `${currentOrientation.charAt(0).toUpperCase() + currentOrientation.slice(1)} Mode`;
        }
    }

    // Download handling
    if (downloadEndcardBtn) {
        downloadEndcardBtn.addEventListener('click', function() {
            if (!currentData) return;

            const filename = `endcard_${currentOrientation}`;
            const htmlContent = currentOrientation === 'portrait' ? currentData.portrait : currentData.landscape;

            fetch(`/download/${currentOrientation}/${filename}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/html'
                },
                body: htmlContent
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || `Download failed: ${response.status}`);
                    });
                }
                return response.blob();
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                const baseName = filename.startsWith('endcard_') ? filename.substring(8) : filename;
                const cleanName = baseName.replace(/\.[^/.]+$/, ''); // Remove file extension
                a.style.display = 'none';
                a.href = url;
                a.download = `${cleanName}_endcard.html`;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    a.remove();
                }, 100);
            })
            .catch(error => {
                console.error('Download failed:', error);
                showError('Failed to download the endcard.');
            });
        });
    }

    // Clear file inputs
    if (clearFileBtn) {
        clearFileBtn.addEventListener('click', function() {
            if (portraitFileInput) portraitFileInput.value = '';
            if (landscapeFileInput) landscapeFileInput.value = '';
            portraitFile = null;
            landscapeFile = null;
            disableElement(combinedUploadBtn);
            hideElement(previewArea);
            hideElement(errorContainer);
            if (mediaPreview) mediaPreview.src = '';
            if (videoPreview) videoPreview.src = '';
        });
    }
});