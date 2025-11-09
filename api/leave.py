from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional # 파이썬 3.9는 List 임포트 필요

from db.database import get_session
from db import crud
from db.models import User, LeaveBalance, LeaveRequest
from schemas.leave import (
    LeaveRequestCreate,
    LeaveRequestRead,
    LeaveBalanceRead,
)
from core.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/leave", tags=["Leave"])

@router.get("/balance", response_model=LeaveBalanceRead)
async def get_my_leave_balance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    로그인된 사용자의 연차 현황을 조회합니다.
    """
    balance = await crud.get_leave_balance_by_user(session, user_id=current_user.id)

    if not balance:
        # 회원가입 시 자동 생성되었어야 함
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave balance data not found.",
        )

    # 남은 연차 일수 계산
    remaining_days = balance.total_granted - balance.total_used

    # 스키마에 맞춰서 응답
    return LeaveBalanceRead(
        total_granted=balance.total_granted,
        total_used=balance.total_used,
        remaining_days=remaining_days,
    )


@router.post("/request", response_model=LeaveRequestRead)
async def create_my_leave_request(
    request_in: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    새로운 연차를 신청합니다.
    """
    # 1. 날짜 검증: start_date가 end_date보다 이전이어야 함
    if request_in.start_date > request_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )

    # 2. 잔여 연차 확인
    balance = await crud.get_leave_balance_by_user(session, user_id=current_user.id)
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave balance data not found"
        )

    remaining_days = balance.total_granted - balance.total_used
    if request_in.days_used > remaining_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient leave balance. You have {remaining_days} days remaining, but requested {request_in.days_used} days."
        )

    # 3. 연차 신청 생성
    new_request = await crud.create_leave_request(
        session=session, user_id=current_user.id, request_in=request_in
    )
    return new_request


@router.get("/requests", response_model=List[LeaveRequestRead])
async def get_my_leave_requests(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    로그인된 사용자의 모든 연차 신청 내역을 조회합니다.
    """
    requests = await crud.get_leave_requests_by_user(
        session=session, user_id=current_user.id
    )
    return requests


# === 관리자 전용 엔드포인트 ===

@router.get("/admin/all-requests", response_model=List[LeaveRequestRead])
async def get_all_leave_requests_admin(
    status_filter: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    [관리자 전용] 모든 사용자의 연차 신청 내역을 조회합니다.
    status_filter: pending, approved, rejected 중 하나 (선택사항)
    """
    requests = await crud.get_all_leave_requests(
        session=session, status=status_filter
    )
    return requests


@router.patch("/admin/approve/{request_id}", response_model=LeaveRequestRead)
async def approve_leave_request_admin(
    request_id: int,
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    [관리자 전용] 연차 신청을 승인합니다.
    승인 시 자동으로 LeaveBalance.total_used가 업데이트됩니다.
    """
    try:
        approved_request = await crud.approve_leave_request(
            session=session, request_id=request_id
        )
        return approved_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/admin/reject/{request_id}", response_model=LeaveRequestRead)
async def reject_leave_request_admin(
    request_id: int,
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    [관리자 전용] 연차 신청을 거부합니다.
    """
    try:
        rejected_request = await crud.reject_leave_request(
            session=session, request_id=request_id
        )
        return rejected_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )