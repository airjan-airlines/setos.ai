#!/usr/bin/env python3
"""
Production startup script for the Paper Roadmap backend API
"""

import uvicorn
import os
import sys
import multiprocessing

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting Paper Roadmap Backend API in PRODUCTION mode...")
    print("Server will be available at: http://0.0.0.0:8000")
    print("API documentation will be available at: http://0.0.0.0:8000/docs")
    
    # Get number of workers (default to 4, or CPU count if available)
    workers = int(os.environ.get('WORKERS', min(4, multiprocessing.cpu_count())))
    
    # Run the FastAPI server with production settings
    uvicorn.run(
        "main:app",  # Changed from app.main:app to main:app
        host="0.0.0.0",
        port=int(os.environ.get('PORT', 8000)),
        workers=workers,
        reload=False,  # Disable auto-reload for production
        log_level="info",  # Less verbose logging
        access_log=True,
        loop="uvloop",  # Use uvloop for better performance
        http="httptools"  # Use httptools for better performance
    )
