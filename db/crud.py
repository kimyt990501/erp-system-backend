from typing import Optional
from datetime import date, time, datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from db.models import (
    User, LeaveBalance, LeaveRequest, SalaryStatement, Attendance
)
from schemas.user import UserCreate
from schemas.leave import LeaveRequestCreate
from schemas.salary import SalaryStatementCreate
from schemas.attendance import AttendanceCreate, CheckInRequest, CheckOutRequest
from core.security import get_password_hash

# 1. 이메일로 유저 찾기
async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()

# 2. 유저 생성 (회원가입)
async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    # 비밀번호 해시
    hashed_password = get_password_hash(user_create.password)
    
    # DB에 저장할 User 객체 생성
    db_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        name=user_create.name,
        hire_date=user_create.hire_date,
        is_active=True
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    
    # (중요) 회원가입 시, 연차 현황(LeaveBalance) 레코드도 생성
    db_leave_balance = LeaveBalance(user_id=db_user.id)
    session.add(db_leave_balance)
    await session.commit()
    await session.refresh(db_user) # user 객체에 leave_balance 관계 반영

    return db_user

# 3. ID로 연차 현황 조회
async def get_leave_balance_by_user(
    session: AsyncSession, user_id: int
) -> Optional[LeaveBalance]:
    statement = select(LeaveBalance).where(LeaveBalance.user_id == user_id)
    result = await session.exec(statement)
    return result.first()

# 4. 연차 신청 내역 조회
async def get_leave_requests_by_user(
    session: AsyncSession, user_id: int
) -> list[LeaveRequest]:
    statement = (
        select(LeaveRequest)
        .where(LeaveRequest.user_id == user_id)
        .order_by(LeaveRequest.start_date.desc()) # 최근 신청 순
    )
    result = await session.exec(statement)
    return result.all()

# 5. 연차 신청 생성
async def create_leave_request(
    session: AsyncSession, user_id: int, request_in: LeaveRequestCreate
) -> LeaveRequest:
    # 1. 스키마를 DB 모델 객체로 변환
    # (참고: status는 'pending'이 기본값임)
    db_request = LeaveRequest.model_validate(
        request_in, update={"user_id": user_id}
    )
    
    # 2. DB에 추가
    session.add(db_request)
    await session.commit()
    await session.refresh(db_request)

    # (중요)
    # 실제 운영에서는 관리자가 "승인"을 눌렀을 때
    # LeaveBalance.total_used를 업데이트해야 하지만,
    # 지금은 신청 기능만 먼저 구현합니다.

    return db_request

# 6. 급여 명세서 목록 조회
async def get_salary_statements_by_user(
    session: AsyncSession, user_id: int
) -> list[SalaryStatement]:
    statement = (
        select(SalaryStatement)
        .where(SalaryStatement.user_id == user_id)
        .order_by(SalaryStatement.pay_month.desc()) # 최근 지급월 순
    )
    result = await session.exec(statement)
    return result.all()

# 7. 급여 명세서 생성 (입력)
async def create_salary_statement(
    session: AsyncSession, user_id: int, statement_in: SalaryStatementCreate
) -> SalaryStatement:
    
    # 1. 스키마를 DB 모델 객체로 변환
    db_statement = SalaryStatement.model_validate(
        statement_in, update={"user_id": user_id}
    )
    
    # 2. DB에 추가
    session.add(db_statement)
    await session.commit()
    await session.refresh(db_statement)

    return db_statement

# 8. 연차 신청 ID로 조회
async def get_leave_request_by_id(
    session: AsyncSession, request_id: int
) -> Optional[LeaveRequest]:
    statement = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await session.exec(statement)
    return result.first()

# 9. 연차 승인 처리 (관리자 전용)
async def approve_leave_request(
    session: AsyncSession, request_id: int
) -> LeaveRequest:
    # 1. 연차 신청 조회
    statement = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await session.exec(statement)
    leave_request = result.first()

    if not leave_request:
        raise ValueError("Leave request not found")

    if leave_request.status != "pending":
        raise ValueError("Only pending requests can be approved")

    # 2. 상태를 approved로 변경
    leave_request.status = "approved"

    # 3. LeaveBalance의 total_used 업데이트
    balance_statement = select(LeaveBalance).where(
        LeaveBalance.user_id == leave_request.user_id
    )
    balance_result = await session.exec(balance_statement)
    leave_balance = balance_result.first()

    if leave_balance:
        leave_balance.total_used += leave_request.days_used

    await session.commit()
    await session.refresh(leave_request)

    return leave_request

# 10. 연차 거부 처리 (관리자 전용)
async def reject_leave_request(
    session: AsyncSession, request_id: int
) -> LeaveRequest:
    # 1. 연차 신청 조회
    statement = select(LeaveRequest).where(LeaveRequest.id == request_id)
    result = await session.exec(statement)
    leave_request = result.first()

    if not leave_request:
        raise ValueError("Leave request not found")

    if leave_request.status != "pending":
        raise ValueError("Only pending requests can be rejected")

    # 2. 상태를 rejected로 변경
    leave_request.status = "rejected"

    await session.commit()
    await session.refresh(leave_request)

    return leave_request

# 11. 전체 사용자 목록 조회 (관리자 전용)
async def get_all_users(session: AsyncSession) -> list[User]:
    statement = select(User).order_by(User.id)
    result = await session.exec(statement)
    return result.all()

# 12. 전체 연차 신청 목록 조회 (관리자 전용)
async def get_all_leave_requests(
    session: AsyncSession, status: Optional[str] = None
) -> list[LeaveRequest]:
    statement = select(LeaveRequest)

    if status:
        statement = statement.where(LeaveRequest.status == status)

    statement = statement.order_by(LeaveRequest.start_date.desc())
    result = await session.exec(statement)
    return result.all()

# ============ 근태 관리 CRUD 함수들 ============

# 13. 출근 체크인
async def check_in_attendance(
    session: AsyncSession, user_id: int, work_date: date, check_in_time: time, notes: Optional[str] = None
) -> Attendance:
    """
    출근 체크인을 기록합니다.
    이미 해당 날짜에 기록이 있으면 에러를 발생시킵니다.
    """
    # 이미 체크인 기록이 있는지 확인
    existing = await get_attendance_by_user_and_date(session, user_id, work_date)
    if existing:
        raise ValueError("Already checked in for this date")

    # 지각 판정: 09:00 이후 출근은 지각
    standard_time = time(9, 0)
    status = "late" if check_in_time > standard_time else "present"

    attendance = Attendance(
        user_id=user_id,
        work_date=work_date,
        check_in=check_in_time,
        status=status,
        notes=notes
    )
    session.add(attendance)
    await session.commit()
    await session.refresh(attendance)
    return attendance

# 14. 퇴근 체크아웃
async def check_out_attendance(
    session: AsyncSession, user_id: int, work_date: date, check_out_time: time
) -> Attendance:
    """
    퇴근 체크아웃을 기록합니다.
    출근 기록이 없으면 에러를 발생시킵니다.
    """
    attendance = await get_attendance_by_user_and_date(session, user_id, work_date)
    if not attendance:
        raise ValueError("No check-in record found for this date")

    if attendance.check_out:
        raise ValueError("Already checked out for this date")

    # 조퇴 판정: 18:00 이전 퇴근은 조퇴
    standard_time = time(18, 0)
    if check_out_time < standard_time and attendance.status == "present":
        attendance.status = "early_leave"

    attendance.check_out = check_out_time
    attendance.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(attendance)
    return attendance

# 15. 특정 날짜의 근태 기록 조회
async def get_attendance_by_user_and_date(
    session: AsyncSession, user_id: int, work_date: date
) -> Optional[Attendance]:
    statement = select(Attendance).where(
        Attendance.user_id == user_id,
        Attendance.work_date == work_date
    )
    result = await session.exec(statement)
    return result.first()

# 16. 사용자의 근태 기록 목록 조회 (기간별)
async def get_attendances_by_user(
    session: AsyncSession,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> list[Attendance]:
    statement = select(Attendance).where(Attendance.user_id == user_id)

    if start_date:
        statement = statement.where(Attendance.work_date >= start_date)
    if end_date:
        statement = statement.where(Attendance.work_date <= end_date)

    statement = statement.order_by(Attendance.work_date.desc())
    result = await session.exec(statement)
    return result.all()

# 17. 전체 사용자의 근태 기록 조회 (관리자용)
async def get_all_attendances(
    session: AsyncSession,
    work_date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> list[Attendance]:
    statement = select(Attendance).options(selectinload(Attendance.user))

    if work_date:
        statement = statement.where(Attendance.work_date == work_date)
    else:
        if start_date:
            statement = statement.where(Attendance.work_date >= start_date)
        if end_date:
            statement = statement.where(Attendance.work_date <= end_date)

    statement = statement.order_by(Attendance.work_date.desc(), Attendance.user_id)
    result = await session.exec(statement)
    return result.all()

# 18. 근태 통계 조회
async def get_attendance_stats(
    session: AsyncSession,
    user_id: int,
    start_date: date,
    end_date: date
) -> dict:
    """
    특정 기간의 근태 통계를 반환합니다.
    """
    attendances = await get_attendances_by_user(session, user_id, start_date, end_date)

    total_days = len(attendances)
    present_days = sum(1 for a in attendances if a.status == "present")
    late_days = sum(1 for a in attendances if a.status == "late")
    early_leave_days = sum(1 for a in attendances if a.status == "early_leave")
    absent_days = sum(1 for a in attendances if a.status == "absent")

    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0.0

    return {
        "total_days": total_days,
        "present_days": present_days,
        "late_days": late_days,
        "early_leave_days": early_leave_days,
        "absent_days": absent_days,
        "attendance_rate": round(attendance_rate, 2)
    }

# 19. 근태 기록 생성 (관리자용)
async def create_attendance_record(
    session: AsyncSession, user_id: int, attendance_in: AttendanceCreate
) -> Attendance:
    """
    관리자가 직접 근태 기록을 생성합니다.
    """
    # 이미 기록이 있는지 확인
    existing = await get_attendance_by_user_and_date(session, user_id, attendance_in.work_date)
    if existing:
        raise ValueError("Attendance record already exists for this date")

    attendance = Attendance.model_validate(
        attendance_in, update={"user_id": user_id}
    )
    session.add(attendance)
    await session.commit()
    await session.refresh(attendance)
    return attendance