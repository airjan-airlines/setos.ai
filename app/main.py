from fastapi import FastAPI
from app import roadmap
from app.models import RoadmapRequest, RoadmapResponse, SummaryResponse, JargonResponse
from fastapi import HTTPException
from app import llm

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Paper Roadmap API is running"}

@app.post("/roadmap/", response_model=RoadmapResponse)
async def get_roadmap(request: RoadmapRequest):
    generated_roadmap = roadmap.generate_roadmap(request.query)
    return {"roadmap": generated_roadmap}

@app.get("/paper/{paper_id}/summary", response_model=SummaryResponse)
async def get_summary(paper_id: str):
    paper = roadmap.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    summary = llm.generate_response(command = "summary", abstract = paper)
    return {"paper_id": paper_id, "summary": summary}

@app.get("/paper/{paper_id}/jargon", response_model=JargonResponse)
async def get_jargon(paper_id: str):
    paper = roadmap.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    jargon_list = llm.generate_response("jargon", paper)
    return {"paper_id": paper_id, "jargon": jargon_list}