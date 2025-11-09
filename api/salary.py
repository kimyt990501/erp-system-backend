from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List # 파이썬 3.9는 List 임포트 필요

from db.database import get_session
from db import crud
from db.models import User
from schemas.salary import SalaryStatementCreate, SalaryStatementRead
from core.security import get_current_user

router = APIRouter(prefix="/salary", tags=["Salary"])

@router.get("", response_model=List[SalaryStatementRead])
async def get_my_salary_statements(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    로그인된 사용자가 입력한 모든 급여 명세서 내역을 조회합니다.
    """
    statements = await crud.get_salary_statements_by_user(
        session=session, user_id=current_user.id
    )
    return statements


@router.post("", response_model=SalaryStatementRead)
async def create_my_salary_statement(
    statement_in: SalaryStatementCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    새로운 급여 명세서를 입력합니다.
    (예: pay_month: "2025-10")
    """
    new_statement = await crud.create_salary_statement(
        session=session, user_id=current_user.id, statement_in=statement_in
    )
    return new_statement