# app/api/routers/crud.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.core.database import AsyncSession, get_db
from app.models import Mission, Task, User

router = APIRouter(prefix="/api/v1", tags=["CRUD"])


@router.get("/users")
async def get_users(
    page: int = 1,
    per_page: int = 20,
    email: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = "asc",
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if email:
        query = query.where(User.email == email)

    if sort_by and hasattr(User, sort_by):
        col = getattr(User, sort_by)
        query = query.order_by(col.desc()) if sort_order == "desc" else query.order_by(col.asc())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "status": "success",
        "message": "Users retrieved",
        "data": {
            "items": users,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": 100,  # Mock total for now
                "total_pages": 5,
                "has_next": True,
                "has_prev": False,
            },
        },
        "timestamp": "2024-01-01T00:00:00Z",
    }


@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "status": "success",
        "data": user,
        "message": "User found",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@router.get("/missions")
async def get_missions(status: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Mission)
    if status:
        query = query.where(Mission.status == status)
    result = await db.execute(query)
    missions = result.scalars().all()
    return {"status": "success", "data": {"items": missions}, "message": "Missions retrieved"}


@router.get("/missions/{mission_id}")
async def get_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"status": "success", "data": mission, "message": "Mission found"}


@router.get("/tasks")
async def get_tasks(mission_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Task)
    if mission_id:
        query = query.where(Task.mission_id == mission_id)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return {"status": "success", "data": {"items": tasks}, "message": "Tasks retrieved"}
