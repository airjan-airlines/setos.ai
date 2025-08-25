// API configuration
const API_BASE_URL = 'http://localhost:8000';

// API service functions
class ApiService {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const requestOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };

        console.log('Making API request to:', url);
        console.log('Request options:', requestOptions);

        try {
            const response = await fetch(url, requestOptions);
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Generate roadmap from query
    async generateRoadmap(query) {
        return this.makeRequest('/roadmap/', {
            method: 'POST',
            body: JSON.stringify({ query }),
        });
    }

    // Get paper summary
    async getPaperSummary(paperId) {
        return this.makeRequest(`/paper/${paperId}/summary`);
    }

    // Get paper jargon
    async getPaperJargon(paperId) {
        return this.makeRequest(`/paper/${paperId}/jargon`);
    }

    // Health check
    async healthCheck() {
        return this.makeRequest('/health');
    }
}

// Create global API service instance
const apiService = new ApiService();

// Function to generate roadmap results from backend
async function generateRoadmapFromAPI(query) {
    try {
        console.log('Generating roadmap for query:', query);
        const response = await apiService.generateRoadmap(query);
        console.log('Raw response from API:', response);
        
        if (response && response.roadmap) {
            console.log('Roadmap data found, transforming...');
            // Transform backend response to frontend format
            const transformedResults = response.roadmap.map((item, index) => ({
                title: item.paper.title,
                summary: item.summary,
                difficulty: getDifficultyFromCitations(item.paper.citation_count),
                datePublished: item.paper.year?.toString() || '2024',
                pageNumber: '25', // Default since we don't have this data
                topic: item.paper.fields_of_study?.[0] || 'Research',
                citations: item.paper.citation_count?.toString() || '0',
                paperId: item.paper.paper_id,
                authors: item.paper.authors,
                abstract: item.paper.abstract,
                url: item.paper.url,
                vocabulary: item.vocabulary,
                quiz: item.quiz
            }));
            console.log('Transformed results:', transformedResults);
            return transformedResults;
        }
        
        console.log('No roadmap data in response, returning empty array');
        return [];
    } catch (error) {
        console.error('Error generating roadmap:', error);
        return [];
    }
}

// Helper function to determine difficulty based on citation count
function getDifficultyFromCitations(citationCount) {
    if (!citationCount) return 'Intermediate';
    if (citationCount > 1000) return 'Advanced';
    if (citationCount > 100) return 'Intermediate';
    return 'Beginner';
}



// Export functions for use in other files
window.ApiService = ApiService;
window.apiService = apiService;
window.generateRoadmapFromAPI = generateRoadmapFromAPI;
