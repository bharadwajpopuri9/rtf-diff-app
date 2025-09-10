// RTF Comparison Tool - Upload JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag and drop for upload zones
    initializeDragAndDrop();
    
    // Initialize file validation
    initializeFileValidation();
    
    // Initialize progress tracking
    initializeProgressTracking();
});

function initializeDragAndDrop() {
    const uploadZones = document.querySelectorAll('.upload-zone');
    
    uploadZones.forEach(zone => {
        const fileInput = zone.querySelector('input[type="file"]');
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            zone.addEventListener(eventName, () => zone.classList.add('dragover'), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            zone.addEventListener(eventName, () => zone.classList.remove('dragover'), false);
        });
        
        // Handle dropped files
        zone.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            
            if (files.length > 0) {
                // Validate file types
                const validFiles = Array.from(files).filter(file => 
                    file.name.toLowerCase().endsWith('.rtf')
                );
                
                if (validFiles.length !== files.length) {
                    showNotification('Only RTF files are allowed', 'error');
                    return;
                }
                
                // Set files to input
                fileInput.files = e.dataTransfer.files;
                
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
                
                // Update visual state
                zone.classList.add('has-files');
                showNotification(`${files.length} file(s) selected`, 'success');
            }
        }, false);
        
        // Handle click to browse
        zone.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Handle file input change
        fileInput.addEventListener('change', function() {
            updateFileDisplay(this);
            validateForm();
        });
    });
}

function initializeFileValidation() {
    const form = document.getElementById('uploadForm');
    const sourceInput = document.getElementById('source_file');
    const comparisonInput = document.getElementById('comparison_files');
    
    if (!form) return;
    
    // Real-time validation
    [sourceInput, comparisonInput].forEach(input => {
        if (input) {
            input.addEventListener('change', function() {
                validateFileInput(this);
                validateForm();
            });
        }
    });
    
    // Form submission validation
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            showNotification('Please correct the errors before submitting', 'error');
        }
    });
}

function initializeProgressTracking() {
    const form = document.getElementById('uploadForm');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const submitBtn = document.getElementById('submitBtn');
    
    if (!form || !progressContainer) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            showNotification('Please correct the errors before submitting', 'error');
            return;
        }
        
        // Start progress simulation
        startProgress();
        
        // Submit form with AJAX to track progress
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                // Form submission successful, redirect to results
                completeProgress();
                setTimeout(() => {
                    window.location.href = response.url;
                }, 500);
            } else {
                return response.text().then(text => {
                    throw new Error('Upload failed');
                });
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            resetProgress();
            showNotification('Error uploading files. Please try again.', 'error');
        });
    });
    
    function startProgress() {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        progressContainer.style.display = 'block';
        
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) {
                progress = 90;
                clearInterval(progressInterval);
            }
            
            progressBar.style.width = progress + '%';
            progressText.textContent = `Processing... ${Math.round(progress)}%`;
        }, 300);
        
        // Store interval ID for cleanup
        form.progressInterval = progressInterval;
    }
    
    function completeProgress() {
        if (form.progressInterval) {
            clearInterval(form.progressInterval);
        }
        
        progressBar.style.width = '100%';
        progressBar.classList.remove('progress-bar-animated');
        progressBar.classList.add('bg-success');
        progressText.textContent = 'Complete! Redirecting...';
    }
    
    function resetProgress() {
        if (form.progressInterval) {
            clearInterval(form.progressInterval);
        }
        
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-play me-2"></i>Compare Files';
        progressContainer.style.display = 'none';
        progressBar.style.width = '0%';
        progressBar.classList.add('progress-bar-animated');
        progressBar.classList.remove('bg-success');
    }
}

function validateFileInput(input) {
    const files = input.files;
    const errors = [];
    
    if (!files || files.length === 0) {
        if (input.hasAttribute('required')) {
            errors.push('This field is required');
        }
    } else {
        // Check file types
        for (let file of files) {
            if (!file.name.toLowerCase().endsWith('.rtf')) {
                errors.push(`"${file.name}" is not an RTF file`);
            }
            
            // Check file size (15MB limit)
            if (file.size > 15 * 1024 * 1024) {
                errors.push(`"${file.name}" is too large (max 15MB)`);
            }
        }
        
        // Check file count for comparison files
        if (input.name === 'comparison_files' && files.length > 20) {
            errors.push('Maximum 20 comparison files allowed');
        }
    }
    
    // Display errors
    displayFieldErrors(input, errors);
    
    return errors.length === 0;
}

function validateForm() {
    const sourceInput = document.getElementById('source_file');
    const comparisonInput = document.getElementById('comparison_files');
    
    let isValid = true;
    
    if (sourceInput) {
        isValid = validateFileInput(sourceInput) && isValid;
    }
    
    if (comparisonInput) {
        isValid = validateFileInput(comparisonInput) && isValid;
    }
    
    // Check for duplicate files
    if (sourceInput && comparisonInput && sourceInput.files.length > 0 && comparisonInput.files.length > 0) {
        const sourceName = sourceInput.files[0].name;
        const comparisonNames = Array.from(comparisonInput.files).map(f => f.name);
        
        if (comparisonNames.includes(sourceName)) {
            displayFieldErrors(comparisonInput, ['Source file is also in comparison files']);
            isValid = false;
        }
    }
    
    // Enable/disable submit button
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.disabled = !isValid;
    }
    
    return isValid;
}

function updateFileDisplay(input) {
    const files = input.files;
    const zone = input.closest('.upload-zone');
    
    if (files.length > 0) {
        zone.classList.add('has-files');
        
        // Update file name display
        const nameSpan = input.name === 'source_file' ? 
            document.getElementById('sourceFileName') : 
            document.getElementById('comparisonFileNames');
        
        if (nameSpan) {
            if (files.length === 1) {
                nameSpan.textContent = files[0].name;
            } else {
                const names = Array.from(files).map(f => f.name).join(', ');
                nameSpan.textContent = names.length > 100 ? 
                    names.substring(0, 100) + '...' : names;
            }
        }
    } else {
        zone.classList.remove('has-files');
    }
}

function displayFieldErrors(input, errors) {
    // Remove existing error messages
    const existingErrors = input.parentNode.querySelectorAll('.error-message');
    existingErrors.forEach(error => error.remove());
    
    // Add new error messages
    if (errors.length > 0) {
        input.classList.add('is-invalid');
        
        errors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message text-danger small mt-1';
            errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i>${error}`;
            input.parentNode.appendChild(errorDiv);
        });
    } else {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    const icon = type === 'error' ? 'exclamation-triangle' : 'check-circle';
    notification.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Utility functions for other pages
window.RTFComparisonUtils = {
    showNotification,
    validateFileInput,
    preventDefaults
};

// Initialize tooltips if Bootstrap is available
if (typeof bootstrap !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize Bootstrap popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    });
}
