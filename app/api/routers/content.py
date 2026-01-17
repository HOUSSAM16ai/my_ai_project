from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/v1/content", tags=["content"])

class ContentItemResponse(BaseModel):
    id: str
    type: str
    title: Optional[str] = None
    level: Optional[str] = None
    branch: Optional[str] = None
    subject: Optional[str] = None
    year: Optional[int] = None
    lang: Optional[str] = None

class ContentSearchResponse(BaseModel):
    items: List[ContentItemResponse]

@router.get("/search", response_model=ContentSearchResponse)
async def search_content(
    q: Optional[str] = Query(None, description="Search query"),
    level: Optional[str] = None,
    branch: Optional[str] = None,
    subject: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Search content items.
    """
    query_str = "SELECT id, type, title, level, branch, subject, year, lang FROM content_items WHERE 1=1"
    params = {}

    if level:
        query_str += " AND level = :level"
        params["level"] = level

    if branch:
        query_str += " AND branch = :branch"
        params["branch"] = branch

    if subject:
        query_str += " AND subject = :subject"
        params["subject"] = subject

    if q:
        # Simple LIKE search
        query_str += " AND (title LIKE :q OR md_content LIKE :q)"
        params["q"] = f"%{q}%"

    query_str += " LIMIT 50"

    result = await db.execute(text(query_str), params)
    rows = result.fetchall()

    items = []
    for row in rows:
        items.append(ContentItemResponse(
            id=row[0],
            type=row[1],
            title=row[2],
            level=row[3],
            branch=row[4],
            subject=row[5],
            year=row[6],
            lang=row[7]
        ))

    return ContentSearchResponse(items=items)

# --- Hierarchy Options Endpoints ---

@router.get("/options/levels")
async def get_levels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT DISTINCT level FROM content_items WHERE level IS NOT NULL ORDER BY level"))
    return [row[0] for row in result.fetchall()]

@router.get("/options/branches")
async def get_branches(level: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT DISTINCT branch FROM content_items WHERE level = :level AND branch IS NOT NULL ORDER BY branch"),
        {"level": level}
    )
    return [row[0] for row in result.fetchall()]

@router.get("/options/subjects")
async def get_subjects(level: str, branch: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT DISTINCT subject FROM content_items WHERE level = :level AND branch = :branch AND subject IS NOT NULL ORDER BY subject"),
        {"level": level, "branch": branch}
    )
    return [row[0] for row in result.fetchall()]

@router.get("/options/years")
async def get_years(level: str, branch: str, subject: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT DISTINCT year FROM content_items WHERE level = :level AND branch = :branch AND subject = :subject AND year IS NOT NULL ORDER BY year DESC"),
        {"level": level, "branch": branch, "subject": subject}
    )
    return [row[0] for row in result.fetchall()]

@router.get("/options/sets")
async def get_sets(level: str, branch: str, subject: str, year: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT DISTINCT set_name FROM content_items WHERE level = :level AND branch = :branch AND subject = :subject AND year = :year AND set_name IS NOT NULL"),
        {"level": level, "branch": branch, "subject": subject, "year": year}
    )
    return [row[0] for row in result.fetchall()]

@router.get("/options/exercises")
async def get_exercises(level: str, branch: str, subject: str, year: int, set_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, title FROM content_items WHERE level = :level AND branch = :branch AND subject = :subject AND year = :year AND set_name = :set_name ORDER BY id"),
        {"level": level, "branch": branch, "subject": subject, "year": year, "set_name": set_name}
    )
    return [{"id": row[0], "title": row[1]} for row in result.fetchall()]

# -----------------------------------

@router.get("/{id}")
async def get_content(id: str, db: AsyncSession = Depends(get_db)):
    """
    Get content metadata and raw content.
    """
    result = await db.execute(
        text("SELECT id, type, title, level, branch, subject, year, lang, md_content FROM content_items WHERE id = :id"),
        {"id": id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    return {
        "id": row[0],
        "type": row[1],
        "title": row[2],
        "level": row[3],
        "branch": row[4],
        "subject": row[5],
        "year": row[6],
        "lang": row[7],
        "md_content": row[8]
    }

@router.get("/{id}/raw")
async def get_content_raw(id: str, db: AsyncSession = Depends(get_db)):
    """
    Get raw markdown content.
    """
    result = await db.execute(
        text("SELECT md_content FROM content_items WHERE id = :id"),
        {"id": id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")

    return {"content": row[0]}

@router.get("/{id}/solution")
async def get_content_solution(id: str, db: AsyncSession = Depends(get_db)):
    """
    Get official solution.
    """
    result = await db.execute(
        text("SELECT solution_md, steps_json, final_answer FROM content_solutions WHERE content_id = :id"),
        {"id": id}
    )
    row = result.fetchone()

    if not row:
         raise HTTPException(status_code=404, detail="Solution not found")

    return {
        "solution_md": row[0],
        "steps_json": row[1],
        "final_answer": row[2]
    }
