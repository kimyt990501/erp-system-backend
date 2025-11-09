from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from db.database import get_session
from db import crud
from schemas.user import UserCreate, UserRead
from schemas.token import Token
from core.security import create_access_token, verify_password
from core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=UserRead)
async def signup_user(
    user_in: UserCreate, 
    session: AsyncSession = Depends(get_session)
):
    """
    회원가입
    """
    user = await crud.get_user_by_email(session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # crud.py의 create_user 함수 호출
    new_user = await crud.create_user(session, user_create=user_in)
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    session: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    로그인 (JWT 토큰 발급)
    """
    # 1. 유저 확인
    user = await crud.get_user_by_email(session, email=form_data.username) # Form은 username을 ID로 씀
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # 2. 비밀번호 확인
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    # 3. 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")