from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.search_engine.graph import search_graph

router = APIRouter(prefix="/reasoning", tags=["reasoning"])

class SearchRequest(BaseModel):
    query: str
    year: Optional[int] = None
    subject: Optional[str] = None
    branch: Optional[str] = None

class SearchResponse(BaseModel):
    answer: str
    documents: list[str]

@router.post("/search", response_model=SearchResponse)
async def smart_search(request: SearchRequest):
    """
    Executes the Smart Search Graph (LangGraph + LlamaIndex + SQL Fallback).
    """
    filters = {}
    if request.year:
        filters["year"] = request.year
    if request.subject:
        filters["subject"] = request.subject
    # Branch filtering logic can be added here

    initial_state = {
        "query": request.query,
        "filters": filters,
        "documents": [],
        "answer": ""
    }

    # Invoke the graph
    result = await search_graph.ainvoke(initial_state)

    return SearchResponse(
        answer=result.get("answer", ""),
        documents=result.get("documents", [])
    )
