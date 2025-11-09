from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

# 출근 체크인 요청
class CheckInRequest(BaseModel):
    work_date: date
    check_in: time
    notes: Optional[str] = None

# 퇴근 체크아웃 요청
class CheckOutRequest(BaseModel):
    check_out: time

# 근태 기록 생성 (관리자용)
class AttendanceCreate(BaseModel):
    work_date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = "present"
    notes: Optional[str] = None

# 근태 기록 조회 응답
class AttendanceRead(BaseModel):
    id: int
    user_id: int
    work_date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 근태 통계 응답
class AttendanceStats(BaseModel):
    total_days: int
    present_days: int
    late_days: int
    early_leave_days: int
    absent_days: int
    attendance_rate: float  # 출석률 (%)
