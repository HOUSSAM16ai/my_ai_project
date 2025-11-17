from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="Health check")
async def health():
    return {"status": "ok"}
