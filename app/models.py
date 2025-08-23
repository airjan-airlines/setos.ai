
from pydantic import BaseModel
from typing import List, Optional

class RoadmapRequest(BaseModel):
    query: str

class Paper(BaseModel):
    paper_id: str
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int]
    url: Optional[str]
    fields_of_study: Optional[List[str]]
    citation_count: Optional[int]
    reference_count: Optional[int]
    influential_citation_count: Optional[int]

class RoadmapPaper(BaseModel):
    paper: Paper
    summary: str
    vocabulary: List[str]
    quiz: List[str]

class RoadmapResponse(BaseModel):
    roadmap: List[RoadmapPaper]

class SummaryResponse(BaseModel):
    paper_id: str
    summary: str

class JargonTerm(BaseModel):
    term: str
    definition: str

class JargonResponse(BaseModel):
    paper_id: str
    jargon: List[JargonTerm]
