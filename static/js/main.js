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

    // File input change handlers
    [portraitFileInput, landscapeFileInput].forEach(input => {
        input.addEventListener('change', function(e) {
            const file = this.files[0];
            if (!file) return;

            if (this === portraitFileInput) {
                portraitFile = file;
                updatePreview(file, 'portrait');
            } else {
                landscapeFile = file;
                updatePreview(file, 'landscape');
            }

            if (portraitFileInput.files[0] && landscapeFileInput.files[0]) {
                enableElement(combinedUploadBtn);
            }
        });
    });

    function updatePreview(file, orientation) {
        const isVideo = file.type.startsWith('video/');
        const fileURL = URL.createObjectURL(file);

        if (currentOrientation === orientation) {
            if (isVideo) {
                videoPreview.src = fileURL;
                videoPreview.style.display = 'block';
                mediaPreview.style.display = 'none';
            } else {
                mediaPreview.src = fileURL;
                mediaPreview.style.display = 'block';
                videoPreview.style.display = 'none';
            }
            showElement(previewArea);
        }
    }

    // Clear file button handler
    if (clearFileBtn) {
        clearFileBtn.addEventListener('click', function() {
            portraitFileInput.value = '';
            landscapeFileInput.value = '';
            portraitFile = null;
            landscapeFile = null;
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
        downloadEndcardBtn.addEventListener('click', handleDownload);
    }

    function toggleOrientation() {
        currentOrientation = currentOrientation === 'portrait' ? 'landscape' : 'portrait';

        // Update container classes
        previewContainer.classList.remove('portrait-container', 'landscape-container');
        previewContainer.classList.add(`${currentOrientation}-container`);

        // Update status text
        orientationStatus.textContent = `${currentOrientation.charAt(0).toUpperCase() + currentOrientation.slice(1)} Mode`;

        // Update preview
        const currentFile = currentOrientation === 'portrait' ? portraitFile : landscapeFile;
        if (currentFile) {
            updatePreview(currentFile, currentOrientation);
        }
    }

    function handleDownload() {
        const orientation = currentOrientation;
        const file = orientation === 'portrait' ? portraitFile : landscapeFile;

        if (!file) {
            showError('No file available for download');
            return;
        }

        const filename = file.name.split('.')[0];
        const downloadFilename = `${filename}_${orientation}.html`;

        // Create download link
        const link = document.createElement('a');
        link.href = URL.createObjectURL(new Blob([endcardPreview.contentDocument.documentElement.outerHTML], { type: 'text/html' }));
        link.download = downloadFilename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Form submission handler
    combinedUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        hideElement(errorContainer);

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
        .then(response => response.json())
        .then(handleUploadSuccess)
        .catch(handleUploadError);
    });

    function handleUploadSuccess(data) {
        hideElement(loadingIndicator);
        enableElement(combinedUploadBtn);

        if (data.error) {
            throw new Error(data.error);
        }

        if (data.endcard_id) {
            endcardIdField.value = data.endcard_id;
            currentEndcardId = data.endcard_id;
        }

        updateEndcardPreview(data);
        showElement(resultsContainer);
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function handleUploadError(error) {
        hideElement(loadingIndicator);
        enableElement(combinedUploadBtn);
        showError(error.message);
    }

    function updateEndcardPreview(data) {
        if (!endcardPreview) return;

        const doc = endcardPreview.contentDocument || endcardPreview.contentWindow.document;
        doc.open();
        doc.write(currentOrientation === 'portrait' ? data.portrait : data.landscape);
        doc.close();
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
});