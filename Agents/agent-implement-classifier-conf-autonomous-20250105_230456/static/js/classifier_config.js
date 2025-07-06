/**
 * Classifier Configuration Client
 * Handles UI interactions and API communication for classifier configuration
 */

class ClassifierConfigClient {
    constructor() {
        this.apiBase = '/api/config';
        this.classifiers = [];
        this.presets = [];
        this.sortable = null;
        this.init();
    }

    async init() {
        await this.loadClassifiers();
        await this.loadPresets();
        this.initializeSortable();
        this.updatePerformancePreview();
    }

    // API Methods
    async loadClassifiers() {
        try {
            const response = await fetch(`${this.apiBase}/classifiers`);
            const data = await response.json();
            
            if (response.ok) {
                this.classifiers = data.classifiers;
                this.renderClassifiers();
                this.updatePipelineOrder();
            } else {
                this.showError(data.error || 'Failed to load classifiers');
            }
        } catch (error) {
            this.showError('Network error loading classifiers');
            console.error(error);
        }
    }

    async toggleClassifier(name, enabled) {
        try {
            const response = await fetch(`${this.apiBase}/classifiers/${name}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(`${name} ${enabled ? 'enabled' : 'disabled'}`);
                await this.loadClassifiers();
                this.updatePerformancePreview();
            } else {
                this.showError(data.error || 'Failed to update classifier');
                // Revert the toggle
                document.getElementById(`toggle-${name}`).checked = !enabled;
            }
        } catch (error) {
            this.showError('Network error updating classifier');
            console.error(error);
        }
    }

    async updatePipelineOrder(order) {
        try {
            const response = await fetch(`${this.apiBase}/pipeline`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Pipeline order updated');
                this.updatePipelineOrderDisplay();
            } else {
                this.showError(data.error || 'Failed to update pipeline order');
                // Reload to revert order
                await this.loadClassifiers();
            }
        } catch (error) {
            this.showError('Network error updating pipeline');
            console.error(error);
        }
    }

    async loadPresets() {
        try {
            const response = await fetch(`${this.apiBase}/presets`);
            const data = await response.json();
            
            if (response.ok) {
                this.presets = data.presets;
                this.renderPresets();
            } else {
                this.showError(data.error || 'Failed to load presets');
            }
        } catch (error) {
            this.showError('Network error loading presets');
            console.error(error);
        }
    }

    async loadPreset(name) {
        if (!confirm(`Load preset "${name}"? This will override your current configuration.`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/presets/${name}/activate`, {
                method: 'PUT'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(`Loaded preset: ${name}`);
                await this.loadClassifiers();
                await this.loadPresets();
                this.updatePerformancePreview();
            } else {
                this.showError(data.error || 'Failed to load preset');
            }
        } catch (error) {
            this.showError('Network error loading preset');
            console.error(error);
        }
    }

    async savePreset(name, description) {
        try {
            const response = await fetch(`${this.apiBase}/presets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(`Saved preset: ${name}`);
                await this.loadPresets();
                return true;
            } else {
                this.showError(data.error || 'Failed to save preset');
                return false;
            }
        } catch (error) {
            this.showError('Network error saving preset');
            console.error(error);
            return false;
        }
    }

    async deletePreset(name) {
        if (!confirm(`Delete preset "${name}"? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/presets/${name}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(`Deleted preset: ${name}`);
                await this.loadPresets();
            } else {
                this.showError(data.error || 'Failed to delete preset');
            }
        } catch (error) {
            this.showError('Network error deleting preset');
            console.error(error);
        }
    }

    // UI Rendering Methods
    renderClassifiers() {
        const container = document.getElementById('classifier-list');
        container.innerHTML = '';
        
        this.classifiers.forEach(classifier => {
            const card = document.createElement('div');
            card.className = `classifier-card ${!classifier.enabled ? 'disabled' : ''}`;
            card.dataset.name = classifier.name;
            
            const impactClass = `impact-${classifier.performance_impact}`;
            const impactText = ['', 'Minimal', 'Low', 'Medium', 'High', 'Very High'][classifier.performance_impact];
            
            card.innerHTML = `
                <div class="d-flex align-items-center">
                    <span class="drag-handle">
                        <i class="fas fa-grip-vertical"></i>
                    </span>
                    
                    <div class="flex-grow-1">
                        <h5 class="mb-1">${classifier.display_name}</h5>
                        <p class="text-muted mb-2">${classifier.description}</p>
                        <span class="performance-badge ${impactClass}">
                            ${impactText} Impact (${classifier.performance_impact}/5)
                        </span>
                    </div>
                    
                    <div class="ms-3">
                        <label class="toggle-switch">
                            <input type="checkbox" 
                                   id="toggle-${classifier.name}"
                                   ${classifier.enabled ? 'checked' : ''}
                                   ${!classifier.can_disable && classifier.enabled ? 'disabled' : ''}
                                   onchange="configClient.toggleClassifier('${classifier.name}', this.checked)">
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    renderPresets() {
        const container = document.getElementById('preset-list');
        container.innerHTML = '';
        
        this.presets.forEach(preset => {
            const card = document.createElement('div');
            card.className = 'preset-card';
            
            const systemBadge = preset.is_system ? 
                '<span class="badge bg-secondary ms-2">System</span>' : '';
            const defaultBadge = preset.is_default ? 
                '<span class="badge bg-primary ms-2">Default</span>' : '';
            
            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1" onclick="configClient.loadPreset('${preset.name}')" style="cursor: pointer;">
                        <h6 class="mb-1">
                            ${preset.name}${systemBadge}${defaultBadge}
                        </h6>
                        <small class="text-muted">${preset.description}</small>
                    </div>
                    ${!preset.is_system ? `
                        <button class="btn btn-sm btn-outline-danger ms-2" 
                                onclick="event.stopPropagation(); configClient.deletePreset('${preset.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
            `;
            
            container.appendChild(card);
        });
    }

    initializeSortable() {
        const container = document.getElementById('classifier-list');
        
        this.sortable = Sortable.create(container, {
            animation: 150,
            handle: '.drag-handle',
            draggable: '.classifier-card',
            onEnd: (evt) => {
                // Get new order
                const items = container.querySelectorAll('.classifier-card');
                const newOrder = Array.from(items).map(item => item.dataset.name);
                
                // Update order via API
                this.updatePipelineOrder(newOrder);
            }
        });
    }

    updatePipelineOrderDisplay() {
        const container = document.getElementById('pipeline-order');
        container.innerHTML = '';
        
        const enabledClassifiers = this.classifiers.filter(c => c.enabled);
        
        enabledClassifiers.forEach((classifier, index) => {
            const li = document.createElement('li');
            li.textContent = classifier.display_name;
            container.appendChild(li);
        });
    }

    updatePerformancePreview() {
        const enabledClassifiers = this.classifiers.filter(c => c.enabled);
        const totalImpact = enabledClassifiers.reduce((sum, c) => sum + c.performance_impact, 0);
        const maxPossibleImpact = this.classifiers.length * 5;
        const impactPercentage = (totalImpact / maxPossibleImpact) * 100;
        
        // Estimate processing time (rough approximation)
        const baseTime = 10;
        const impactMultiplier = 20;
        const estimatedTime = baseTime + (totalImpact * impactMultiplier);
        
        document.getElementById('enabled-count').textContent = enabledClassifiers.length;
        document.getElementById('total-impact').textContent = totalImpact;
        document.getElementById('est-time').textContent = `${estimatedTime}ms`;
        document.getElementById('performance-fill').style.width = `${impactPercentage}%`;
    }

    // Toast Notifications
    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'danger');
    }

    showToast(message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        const container = document.getElementById('toast-container');
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        container.appendChild(toastElement);
        
        const toast = new bootstrap.Toast(toastElement.querySelector('.toast'));
        toast.show();
        
        // Remove after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Global instance
let configClient;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    configClient = new ClassifierConfigClient();
});

// Global functions for HTML onclick handlers
function saveAsPreset() {
    const modal = new bootstrap.Modal(document.getElementById('savePresetModal'));
    modal.show();
}

async function confirmSavePreset() {
    const name = document.getElementById('preset-name').value.trim();
    const description = document.getElementById('preset-description').value.trim();
    
    if (!name) {
        configClient.showError('Please enter a preset name');
        return;
    }
    
    if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
        configClient.showError('Invalid preset name. Use letters, numbers, underscores, and hyphens only.');
        return;
    }
    
    const success = await configClient.savePreset(name, description);
    
    if (success) {
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('savePresetModal'));
        modal.hide();
        
        // Clear form
        document.getElementById('preset-name').value = '';
        document.getElementById('preset-description').value = '';
    }
}