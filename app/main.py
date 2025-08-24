from fastapi import FastAPI
from app import roadmap
from app.models import RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse
from fastapi import HTTPException
from app import llm

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5500", "http://127.0.0.1:5500"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for roadmap generation
class RoadmapRequest(BaseModel):
    query: str

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
        return roadmap
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Backend services not ready: {str(e)}")

@app.post("/roadmap/")
async def get_roadmap(request: RoadmapRequest):
    roadmap = get_roadmap_module()
    
    # Validate request
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        generated_roadmap = roadmap.generate_roadmap(request.query)
        return {"roadmap": generated_roadmap}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating roadmap: {str(e)}")

@app.get("/paper/{paper_id}/summary")
async def get_summary(paper_id: str):
    roadmap = get_roadmap_module()
    
    try:
        paper = roadmap.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        summary = llm.generate_response(command="summary", abstract=paper.abstract)
        return {"paper_id": paper_id, "summary": summary}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.get("/paper/{paper_id}/jargon")
async def get_jargon(paper_id: str):
    roadmap = get_roadmap_module()
    
    try:
        paper = roadmap.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        jargon_list = llm.generate_response("jargon", paper.abstract)
        return {"paper_id": paper_id, "jargon": jargon_list}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting jargon: {str(e)}")
