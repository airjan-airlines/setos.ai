// API client for communicating with the backend
class PaperRoadmapAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    // Generate a roadmap for a given query
    async generateRoadmap(query) {
        try {
            const response = await fetch(`${this.baseURL}/roadmap/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error generating roadmap:', error);
            throw error;
        }
    }

    // Get summary for a specific paper
    async getPaperSummary(paperId) {
        try {
            const response = await fetch(`${this.baseURL}/paper/${paperId}/summary`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting paper summary:', error);
            throw error;
        }
    }

    // Get jargon for a specific paper
    async getPaperJargon(paperId) {
        try {
            const response = await fetch(`${this.baseURL}/paper/${paperId}/jargon`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting paper jargon:', error);
            throw error;
        }
    }

    // Check if backend is running
    async checkBackendHealth() {
        try {
            const response = await fetch(`${this.baseURL.replace('/api', '')}/`);
            return response.ok;
        } catch (error) {
            console.error('Backend health check failed:', error);
            return false;
        }
    }
}

// Create a global instance
window.paperRoadmapAPI = new PaperRoadmapAPI();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PaperRoadmapAPI;
}
