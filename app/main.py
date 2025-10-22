from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app import llm
import os
from typing import Optional
from supabase import Client
from gotrue.errors import AuthApiError
from gotrue import User

from app import roadmap
from app.models import RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse, AbstractResponse
from . import database

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock user for development when authentication is disabled
class MockUser:
    id: str = "mock_user_id"
    email: str = "test@example.com"

# Dependency to get the current user from the Supabase JWT
async def get_current_user(request: Request, client: Client = Depends(database.get_python_client)) -> User:
    try:
        user = client.auth.get_user()
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {e.message}")

# Dependency to make authentication optional for development
async def get_optional_user(request: Request, client: Client = Depends(database.get_python_client)) -> User:
    if os.getenv("DISABLE_AUTH") == "true":
        return MockUser()
    return await get_current_user(request, client)


@app.get("/api/")
def read_root():
    return {"message": "Paper Roadmap API is running"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/api/test")
def test_endpoint():
    return {"message": "Test endpoint working"}

@app.post(path="/api/roadmap/", response_model=RoadmapResponse)
async def get_roadmap(request: RoadmapRequest, client: Client = Depends(database.get_python_client), user: User = Depends(get_optional_user)):
    print(f"Request from user: {user.id}")
    generated_roadmap = roadmap.generate_roadmap(request.query, client)
    return {"roadmap": generated_roadmap}

@app.get("/api/paper/{paper_id}/summary", response_model=SummaryResponse)
async def get_summary(paper_id: str, client: Client = Depends(database.get_python_client), user: User = Depends(get_optional_user)):
    print(f"Request from user: {user.id}")
    paper = roadmap.get_paper_by_id(paper_id, client)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    summary = llm.generate_response(command = "summary", abstract = paper.abstract)
    return {"paper_id": paper_id, "summary": summary}

@app.get("/api/paper/{paper_id}/jargon", response_model=JargonResponse)
async def get_jargon(paper_id: str, client: Client = Depends(database.get_python_client), user: User = Depends(get_optional_user)):
    print(f"Request from user: {user.id}")
    paper = roadmap.get_paper_by_id(paper_id, client)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    jargon_list = llm.generate_response("jargon", paper.abstract)
    return {"paper_id": paper_id, "jargon": jargon_list}

@app.get("/api/paper/{paper_id}/abstract", response_model=AbstractResponse)
async def get_abstract(paper_id: str, client: Client = Depends(database.get_python_client), user: User = Depends(get_optional_user)):
    print(f"Request from user: {user.id}")
    paper = roadmap.get_paper_by_id(paper_id, client)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return {"paper_id": paper_id, "abstract": paper.abstract}