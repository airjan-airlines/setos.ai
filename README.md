# Setos

A web application that generates personalized learning roadmaps from research papers using AI-powered semantic search and natural language processing.

## Features

- **Semantic Search**: Find relevant research papers using AI-powered embeddings
- **Learning Roadmaps**: Generate personalized learning paths from paper collections
- **AI Summaries**: Get plain-language summaries of complex research papers
- **Jargon Extraction**: Identify and explain technical terms from papers
- **Interactive UI**: Modern, responsive web interface

## Usage

1. **Search for a topic**: Enter a research topic or question in the search bar
2. **Generate roadmap**: The system will find relevant papers and create a learning path
3. **Explore papers**: Click on papers to view summaries, key terms, and quizzes
4. **Track progress**: Mark papers as completed and track your learning progress

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
