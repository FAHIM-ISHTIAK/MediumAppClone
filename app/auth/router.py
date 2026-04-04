from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import UserInfo
from app.auth.service import sync_user, verify_supabase_token
from app.dependencies import get_current_user, get_db, security


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sync", response_model=UserInfo)
async def sync_current_user(
    credentials=Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserInfo:
    payload = verify_supabase_token(credentials.credentials)
    user = await sync_user(db, payload)
    return UserInfo.model_validate(user)


@router.get("/me", response_model=UserInfo)
async def get_me(current_user=Depends(get_current_user)) -> UserInfo:
    return UserInfo.model_validate(current_user)
