from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from core.config import settings
from db.database import get_session
from db.models import User
from schemas.token import TokenData

# 1. 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. "로그인 API 주소"를 OAuth2에 알려줌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# 3. 비밀번호 검증
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 4. 비밀번호 해시 생성
def get_password_hash(password):
    return pwd_context.hash(password)

# 5. Access Token 생성
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# 6. (핵심) 현재 로그인한 사용자를 확인하는 Dependency
async def get_current_user(
    session: AsyncSession = Depends(get_session), 
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # DB에서 실제 사용자 확인
    statement = select(User).where(User.email == token_data.email)
    result = await session.exec(statement)
    user = result.first()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

# 7. 관리자 권한 확인 Dependency
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 사용자가 관리자인지 확인합니다.
    관리자가 아니면 403 Forbidden 에러를 발생시킵니다.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user