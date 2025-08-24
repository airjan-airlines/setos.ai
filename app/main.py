from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Paper Roadmap API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

# Import roadmap module only when needed to avoid startup issues
def get_roadmap_module():
    try:
        from app import roadmap
        from app.models import RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse
        return roadmap, RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Backend services not ready: {str(e)}")

@app.post("/roadmap/")
async def get_roadmap(request):
    roadmap, RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse = get_roadmap_module()
    
    # Validate request
    if not hasattr(request, 'query') or not request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        generated_roadmap = roadmap.generate_roadmap(request.query)
        return {"roadmap": generated_roadmap}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating roadmap: {str(e)}")

@app.get("/paper/{paper_id}/summary")
async def get_summary(paper_id: str):
    roadmap, RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse = get_roadmap_module()
    
    try:
        paper = roadmap.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        summary = roadmap.generate_summary_for_paper(paper)
        return {"paper_id": paper_id, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.get("/paper/{paper_id}/jargon")
async def get_jargon(paper_id: str):
    roadmap, RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse = get_roadmap_module()
    
    try:
        paper = roadmap.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        jargon_list = roadmap.extract_jargon_for_paper(paper)
        return {"paper_id": paper_id, "jargon": jargon_list}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting jargon: {str(e)}")