@echo off
echo Starting Paper Roadmap Backend API...
echo.
echo Make sure you have:
echo 1. Python installed and in your PATH
echo 2. Dependencies installed (pip install -r requirements.txt)
echo 3. .env file configured with your API keys
echo 4. PostgreSQL database running with pgvector extension
echo.
echo Server will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python start_backend.py

pause
