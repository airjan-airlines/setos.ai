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
        // Fallback to mock data if API fails
        return generateMockResults(query);
    }
}

// Helper function to determine difficulty based on citation count
function getDifficultyFromCitations(citationCount) {
    if (!citationCount) return 'Intermediate';
    if (citationCount > 1000) return 'Advanced';
    if (citationCount > 100) return 'Intermediate';
    return 'Beginner';
}

// Fallback function to generate mock results
function generateMockResults(query) {
    const topics = ['Machine Learning', 'Data Science', 'Computer Vision', 'Natural Language Processing', 'Robotics', 'Quantum Computing'];
    const difficulties = ['Beginner', 'Intermediate', 'Advanced'];
    const results = [];

    // Create a simple hash from the query to make results deterministic
    let hash = 0;
    for (let i = 0; i < query.length; i++) {
        const char = query.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    
    // Use hash to seed the selection
    const seed = Math.abs(hash);

    for (let i = 0; i < 6; i++) {
        const topicIndex = (seed + i * 7) % topics.length;
        const difficultyIndex = (seed + i * 11) % difficulties.length;
        const topic = topics[topicIndex];
        const difficulty = difficulties[difficultyIndex];
        
        // Generate deterministic values based on seed and index
        const yearOffset = (seed + i * 13) % 5;
        const pageOffset = (seed + i * 17) % 30;
        const citationOffset = (seed + i * 19) % 2000;
        
        results.push({
            title: `${topic} Research Paper ${i + 1}`,
            summary: `This paper explores various aspects of ${topic.toLowerCase()} and its applications in modern technology. The research provides valuable insights into current trends and future directions.`,
            difficulty: difficulty,
            datePublished: (2020 + yearOffset).toString(),
            pageNumber: (20 + pageOffset).toString(),
            topic: topic,
            citations: (100 + citationOffset).toString(),
            paperId: `mock-paper-${i}`,
            authors: ['Research Team'],
            abstract: `This is a mock abstract for ${topic} research paper ${i + 1}.`,
            url: '#',
            vocabulary: ['Key Concept 1', 'Key Concept 2', 'Key Concept 3'],
            quiz: ['What is the main topic?', 'What are the key findings?', 'How is this research significant?']
        });
    }

    return results;
}

// Export functions for use in other files
window.ApiService = ApiService;
window.apiService = apiService;
window.generateRoadmapFromAPI = generateRoadmapFromAPI;
window.generateMockResults = generateMockResults;
