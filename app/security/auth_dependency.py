from fastapi import Depends
from app.deps.auth import get_current_user

async def get_current_active_user(current=Depends(get_current_user)):
    return current.user

async def get_current_admin(current=Depends(get_current_user)):
    if not current.user.is_admin:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current.user
