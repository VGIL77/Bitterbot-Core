// Dashboard configuration for different environments
const DASHBOARD_CONFIG = {
    // Auto-detect environment based on hostname
    getApiUrl() {
        const hostname = window.location.hostname;
        
        // Production (Railway)
        if (hostname.includes('railway.app')) {
            return `https://${hostname}`;
        }
        
        // Local development
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }
        
        // Default to same origin
        return '';
    },
    
    getWebSocketUrl() {
        const apiUrl = this.getApiUrl();
        return apiUrl.replace('https://', 'wss://').replace('http://', 'ws://');
    },
    
    endpoints: {
        login: '/api/admin/login',
        metrics: '/api/engrams/metrics',
        threads: '/api/engrams/threads',
        history: (threadId) => `/api/engrams/${threadId}/history`,
        events: '/api/events'
    }
};

// Export for use in other scripts
window.DASHBOARD_CONFIG = DASHBOARD_CONFIG;