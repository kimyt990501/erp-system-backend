from sqlmodel import SQLModel
from datetime import date
from db.models import User  # User 모델 참조

# 회원가입 시 받을 데이터 (비밀번호 포함)
class UserCreate(SQLModel):
    email: str
    password: str
    name: str
    hire_date: date

# API가 응답할 (보여줄) 유저 데이터 (비밀번호 제외)
class UserRead(SQLModel):
    id: int
    email: str
    name: str
    hire_date: date
    is_active: bool
    role: str