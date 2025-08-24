# Paper Roadmap

A web application that generates personalized learning roadmaps from research papers using AI-powered semantic search and natural language processing.

## Features

- **Semantic Search**: Find relevant research papers using AI-powered embeddings
- **Learning Roadmaps**: Generate personalized learning paths from paper collections
- **AI Summaries**: Get plain-language summaries of complex research papers
- **Jargon Extraction**: Identify and explain technical terms from papers
- **Interactive UI**: Modern, responsive web interface

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js (for frontend development server)
- PostgreSQL database with pgvector extension
- Google Generative AI API key

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory with:
   ```
   gemini_key=your_google_generative_ai_api_key_here
   DATABASE_URL=postgresql://username:password@localhost:5432/paper_roadmap
   ```

3. **Set up the database**:
   - Install PostgreSQL and the pgvector extension
   - Create a database named `paper_roadmap`
   - Run the database setup scripts in `app/database.py`

4. **Start the backend server**:
   ```bash
   python start_backend.py
   ```
   
   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Install Node.js dependencies** (if using a development server):
   ```bash
   npm install
   ```

2. **Serve the frontend**:
   You can use any static file server. For development:
   ```bash
   # Using Python's built-in server
   python -m http.server 5500
   
   # Or using Node.js live-server
   npx live-server --port=5500
   ```

3. **Open the application**:
   Navigate to `http://localhost:5500` in your browser

## Usage

1. **Search for a topic**: Enter a research topic or question in the search bar
2. **Generate roadmap**: The system will find relevant papers and create a learning path
3. **Explore papers**: Click on papers to view summaries, key terms, and quizzes
4. **Track progress**: Mark papers as completed and track your learning progress

## API Endpoints

- `POST /roadmap/` - Generate a learning roadmap for a query
- `GET /paper/{paper_id}/summary` - Get a summary of a specific paper
- `GET /paper/{paper_id}/jargon` - Get technical terms from a paper
- `GET /health` - Health check endpoint

## Architecture

- **Backend**: FastAPI with Python
- **Frontend**: HTML/CSS/JavaScript with modern UI
- **Database**: PostgreSQL with pgvector for embeddings
- **AI**: Google Generative AI for summaries and jargon extraction
- **Embeddings**: SciBERT for semantic search

## Development

- Backend code is in the `app/` directory
- Frontend files are in the root directory
- API documentation is auto-generated at `/docs` when the server is running

## Troubleshooting

- **API connection issues**: Make sure the backend server is running on port 8000
- **Database errors**: Check your PostgreSQL connection and pgvector installation
- **AI generation failures**: Verify your Google Generative AI API key is valid
- **CORS errors**: The backend is configured to allow requests from common development ports
