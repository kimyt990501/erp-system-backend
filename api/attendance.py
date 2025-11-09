from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional
from datetime import date, time, datetime, timezone

from db.database import get_session
from db import crud
from db.models import User, Attendance
from schemas.attendance import (
    CheckInRequest,
    CheckOutRequest,
    AttendanceCreate,
    AttendanceRead,
    AttendanceStats,
)
from core.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/check-in", response_model=AttendanceRead)
async def check_in(
    check_in_data: CheckInRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    출근 체크인을 합니다.
    - work_date: 근무일 (기본값: 오늘)
    - check_in: 출근 시각
    - 09:00 이후 출근 시 자동으로 '지각'으로 표시됩니다.
    """
    try:
        attendance = await crud.check_in_attendance(
            session=session,
            user_id=current_user.id,
            work_date=check_in_data.work_date,
            check_in_time=check_in_data.check_in,
            notes=check_in_data.notes,
        )
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.patch("/check-out", response_model=AttendanceRead)
async def check_out(
    check_out_data: CheckOutRequest,
    work_date: date = Query(..., description="퇴근할 근무일"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    퇴근 체크아웃을 합니다.
    - work_date: 근무일 (쿼리 파라미터)
    - check_out: 퇴근 시각
    - 18:00 이전 퇴근 시 자동으로 '조퇴'로 표시됩니다.
    """
    try:
        attendance = await crud.check_out_attendance(
            session=session,
            user_id=current_user.id,
            work_date=work_date,
            check_out_time=check_out_data.check_out,
        )
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/my-records", response_model=List[AttendanceRead])
async def get_my_attendance_records(
    start_date: Optional[date] = Query(None, description="조회 시작일"),
    end_date: Optional[date] = Query(None, description="조회 종료일"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    로그인한 사용자의 근태 기록을 조회합니다.
    - start_date, end_date로 기간 필터링 가능
    """
    attendances = await crud.get_attendances_by_user(
        session=session,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    return attendances


@router.get("/my-stats", response_model=AttendanceStats)
async def get_my_attendance_stats(
    start_date: date = Query(..., description="통계 시작일"),
    end_date: date = Query(..., description="통계 종료일"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    로그인한 사용자의 근태 통계를 조회합니다.
    - 지정한 기간 내의 출석률, 지각/조퇴/결근 일수 등을 반환합니다.
    """
    stats = await crud.get_attendance_stats(
        session=session,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
    return AttendanceStats(**stats)


@router.get("/today", response_model=AttendanceRead)
async def get_today_attendance(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    오늘의 근태 기록을 조회합니다.
    """
    today = date.today()
    attendance = await crud.get_attendance_by_user_and_date(
        session=session, user_id=current_user.id, work_date=today
    )
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance record for today",
        )
    return attendance


# === 관리자 전용 엔드포인트 ===


@router.get("/admin/all-records", response_model=List[AttendanceRead])
async def get_all_attendance_records_admin(
    work_date: Optional[date] = Query(None, description="특정 날짜 조회"),
    start_date: Optional[date] = Query(None, description="조회 시작일"),
    end_date: Optional[date] = Query(None, description="조회 종료일"),
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    [관리자 전용] 전체 사용자의 근태 기록을 조회합니다.
    - work_date: 특정 날짜만 조회
    - start_date, end_date: 기간으로 조회
    """
    attendances = await crud.get_all_attendances(
        session=session,
        work_date=work_date,
        start_date=start_date,
        end_date=end_date,
    )
    return attendances


@router.post("/admin/create/{user_id}", response_model=AttendanceRead)
async def create_attendance_record_admin(
    user_id: int,
    attendance_in: AttendanceCreate,
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    [관리자 전용] 특정 사용자의 근태 기록을 직접 생성합니다.
    - 결근 처리나 수동 기록 입력 시 사용
    """
    try:
        attendance = await crud.create_attendance_record(
            session=session, user_id=user_id, attendance_in=attendance_in
        )
        return attendance
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/admin/user/{user_id}/stats", response_model=AttendanceStats)
async def get_user_attendance_stats_admin(
    user_id: int,
    start_date: date = Query(..., description="통계 시작일"),
    end_date: date = Query(..., description="통계 종료일"),
    current_admin: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    [관리자 전용] 특정 사용자의 근태 통계를 조회합니다.
    """
    stats = await crud.get_attendance_stats(
        session=session,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    return AttendanceStats(**stats)
