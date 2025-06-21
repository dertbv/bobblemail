// Main JavaScript for Penny Stock Analysis Web App

// Global configuration
const API_BASE_URL = '';
const POLLING_INTERVAL = 3000; // 3 seconds

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value / 100);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// API wrapper functions
const API = {
    async get(endpoint) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            return await response.json();
        } catch (error) {
            console.error(`API GET error for ${endpoint}:`, error);
            throw error;
        }
    },

    async post(endpoint, data = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`API POST error for ${endpoint}:`, error);
            throw error;
        }
    },

    async startAnalysis() {
        return this.post('/api/start-analysis');
    },

    async getAnalysisStatus() {
        return this.get('/api/analysis-status');
    },

    async getResults() {
        return this.get('/api/results');
    },

    async getStockDetails(ticker) {
        return this.get(`/api/stock/${ticker}`);
    },

    async healthCheck() {
        return this.get('/api/health');
    }
};

// Analysis manager
class AnalysisManager {
    constructor() {
        this.pollingInterval = null;
        this.isPolling = false;
    }

    async startAnalysis() {
        try {
            const result = await API.startAnalysis();
            if (result.status === 'success') {
                this.startPolling();
                return result;
            } else {
                throw new Error(result.message || 'Failed to start analysis');
            }
        } catch (error) {
            console.error('Error starting analysis:', error);
            throw error;
        }
    }

    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        this.pollingInterval = setInterval(async () => {
            try {
                const status = await API.getAnalysisStatus();
                this.handleStatusUpdate(status);
                
                if (!status.in_progress) {
                    this.stopPolling();
                }
            } catch (error) {
                console.error('Error polling status:', error);
                this.stopPolling();
            }
        }, POLLING_INTERVAL);
    }

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
    }

    handleStatusUpdate(status) {
        // Emit custom event for status updates
        const event = new CustomEvent('analysisStatusUpdate', {
            detail: status
        });
        document.dispatchEvent(event);
    }
}

// Notification system
class NotificationManager {
    static show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 1050;
            min-width: 300px;
            max-width: 500px;
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
    }

    static success(message, duration = 5000) {
        this.show(message, 'success', duration);
    }

    static error(message, duration = 8000) {
        this.show(message, 'danger', duration);
    }

    static warning(message, duration = 6000) {
        this.show(message, 'warning', duration);
    }

    static info(message, duration = 5000) {
        this.show(message, 'info', duration);
    }
}

// Chart utilities
class ChartUtils {
    static createScoreChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.ticker),
                datasets: [{
                    label: 'Technical',
                    data: data.map(item => item.technical_score),
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }, {
                    label: 'Fundamental',
                    data: data.map(item => item.fundamental_score),
                    backgroundColor: 'rgba(255, 99, 132, 0.8)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }, {
                    label: 'Sentiment',
                    data: data.map(item => item.sentiment_score),
                    backgroundColor: 'rgba(75, 192, 192, 0.8)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    static createUpsideChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const topFive = data.slice(0, 5);
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: topFive.map(item => item.ticker),
                datasets: [{
                    data: topFive.map(item => item.upside_potential),
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }
}

// Data validation utilities
class ValidationUtils {
    static isValidStock(stock) {
        return stock && 
               typeof stock.ticker === 'string' &&
               typeof stock.current_price === 'number' &&
               typeof stock.target_price === 'number' &&
               typeof stock.composite_score === 'number';
    }

    static sanitizeStockData(stock) {
        return {
            ticker: String(stock.ticker || '').toUpperCase(),
            current_price: Number(stock.current_price || 0),
            target_price: Number(stock.target_price || 0),
            upside_potential: Number(stock.upside_potential || 0),
            composite_score: Number(stock.composite_score || 0),
            technical_score: Number(stock.technical_score || 0),
            fundamental_score: Number(stock.fundamental_score || 0),
            sentiment_score: Number(stock.sentiment_score || 0)
        };
    }
}

// Initialize global instances
const analysisManager = new AnalysisManager();

// Global event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states to buttons
    document.querySelectorAll('button[data-loading-text]').forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            const loadingText = this.getAttribute('data-loading-text');
            
            this.innerHTML = loadingText;
            this.disabled = true;
            
            // Reset after 30 seconds as fallback
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 30000);
        });
    });
});

// Handle analysis status updates
document.addEventListener('analysisStatusUpdate', function(event) {
    const status = event.detail;
    console.log('Analysis status update:', status);
    
    // You can add global status handling here
    if (status.has_results && !status.in_progress) {
        NotificationManager.success('Analysis completed successfully!');
    }
});

// Export for use in other scripts
window.PennyStockApp = {
    API,
    AnalysisManager,
    NotificationManager,
    ChartUtils,
    ValidationUtils,
    analysisManager,
    formatCurrency,
    formatPercentage,
    formatDate
};