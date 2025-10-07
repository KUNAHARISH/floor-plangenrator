class FloorPlanGenerator {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.loadHistory();
    }

    initializeElements() {
        this.uploadForm = document.getElementById('uploadForm');
        this.generateForm = document.getElementById('generateForm');
        this.imageInput = document.getElementById('imageInput');
        this.imagePreview = document.getElementById('imagePreview');
        this.previewImg = document.getElementById('previewImg');
        this.removeImageBtn = document.getElementById('removeImage');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        this.loadingSection = document.getElementById('loadingSection');
        this.resultsSection = document.getElementById('resultsSection');
        this.resultsContent = document.getElementById('resultsContent');
        this.generateSection = document.getElementById('generateSection');
        this.historyContent = document.getElementById('historyContent');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.newAnalysisBtn = document.getElementById('newAnalysisBtn');
    }

    bindEvents() {
        // File input events
        this.imageInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.removeImageBtn.addEventListener('click', () => this.removeImage());
        
        // Form events
        this.uploadForm.addEventListener('submit', (e) => this.handleImageUpload(e));
        this.generateForm.addEventListener('submit', (e) => this.handlePlanGeneration(e));
        
        // Button events
        this.downloadBtn.addEventListener('click', () => this.downloadResults());
        this.newAnalysisBtn.addEventListener('click', () => this.resetForm());

        // Drag and drop events
        this.setupDragAndDrop();
    }

    setupDragAndDrop() {
        const uploadLabel = document.querySelector('.file-upload-label');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadLabel.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadLabel.addEventListener(eventName, () => {
                uploadLabel.style.borderColor = '#667eea';
                uploadLabel.style.background = '#edf2f7';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadLabel.addEventListener(eventName, () => {
                uploadLabel.style.borderColor = '#cbd5e0';
                uploadLabel.style.background = '#f8fafc';
            }, false);
        });

        uploadLabel.addEventListener('drop', (e) => this.handleDrop(e), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            this.imageInput.files = files;
            this.handleFileSelect({ target: { files: files } });
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        
        if (!file) return;

        // Validate file type
        const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/bmp'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Please select a valid image file (PNG, JPG, JPEG, GIF, BMP)');
            return;
        }

        // Validate file size (16MB)
        if (file.size > 16 * 1024 * 1024) {
            this.showError('File size must be less than 16MB');
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            this.previewImg.src = e.target.result;
            this.imagePreview.style.display = 'block';
            this.analyzeBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    removeImage() {
        this.imageInput.value = '';
        this.imagePreview.style.display = 'none';
        this.analyzeBtn.disabled = true;
        this.hideResults();
    }

    async handleImageUpload(e) {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('image', this.imageInput.files[0]);

        this.showLoading();
        
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showResults(result.analysis);
                this.generateSection.style.display = 'block';
                this.loadHistory(); // Refresh history
            } else {
                this.showError(result.error || 'Failed to analyze image');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Upload error:', error);
        } finally {
            this.hideLoading();
        }
    }

    async handlePlanGeneration(e) {
        e.preventDefault();
        
        const requirements = document.getElementById('requirements').value.trim();
        
        if (!requirements) {
            this.showError('Please enter your requirements');
            return;
        }

        this.showLoading();
        
        try {
            const response = await fetch('/generate_plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ requirements })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showResults(result.generated_plan, 'Generated Plan');
                this.loadHistory(); // Refresh history
            } else {
                this.showError(result.error || 'Failed to generate plan');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Generation error:', error);
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        this.loadingSection.style.display = 'block';
        this.resultsSection.style.display = 'none';
    }

    hideLoading() {
        this.loadingSection.style.display = 'none';
    }

    showResults(content, title = 'Analysis Results') {
        this.resultsContent.textContent = content;
        this.resultsSection.style.display = 'block';
        this.hideLoading();
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideResults() {
        this.resultsSection.style.display = 'none';
        this.generateSection.style.display = 'none';
    }

    showError(message) {
        alert(`Error: ${message}`);
    }

    resetForm() {
        this.uploadForm.reset();
        this.generateForm.reset();
        this.removeImage();
        this.hideResults();
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    downloadResults() {
        const content = this.resultsContent.textContent;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `floor-plan-analysis-${new Date().toISOString().slice(0, 19)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    async loadHistory() {
        try {
            const response = await fetch('/history');
            const result = await response.json();
            
            if (result.success && result.files.length > 0) {
                this.displayHistory(result.files);
            } else {
                this.historyContent.innerHTML = '<p class="no-history">No previous analyses found</p>';
            }
        } catch (error) {
            console.error('Error loading history:', error);
            this.historyContent.innerHTML = '<p class="no-history">Error loading history</p>';
        }
    }

    displayHistory(files) {
        const historyHTML = files.slice(0, 5).map(file => `
            <div class="history-item">
                <div>
                    <strong>${file.type === 'analysis' ? 'Image Analysis' : 'Plan Generation'}</strong>
                    <br>
                    <small>${new Date(file.timestamp.replace(/_/g, ':')).toLocaleString()}</small>
                </div>
                <button onclick="window.open('/download/${file.filename}', '_blank')" class="btn-outline" style="padding: 5px 10px; font-size: 0.8rem;">
                    <i class="fas fa-download"></i> Download
                </button>
            </div>
        `).join('');
        
        this.historyContent.innerHTML = historyHTML;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FloorPlanGenerator();
});
