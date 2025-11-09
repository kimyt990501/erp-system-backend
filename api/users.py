from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from db.models import User
from db.database import get_session
from db import crud
from schemas.user import UserRead
from core.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserRead)
async def read_users_me(
    # 이 Dependency가 토큰을 검증하고 로그인된 유저 정보를 반환
    current_user: User = Depends(get_current_user)
):
    """
    로그인된 내 정보 확인
    """
    return current_user


# === 관리자 전용 엔드포인트 ===

@router.get("/admin/all", response_model=List[UserRead])
async def get_all_users_admin(
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    [관리자 전용] 모든 사용자 목록을 조회합니다.
    """
    users = await crud.get_all_users(session)
    return users