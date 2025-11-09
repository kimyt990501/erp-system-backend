from sqlmodel import SQLModel
from datetime import date
from typing import Optional

# 1. 연차 신청 시 받을 데이터
class LeaveRequestCreate(SQLModel):
    start_date: date
    end_date: date
    days_used: float
    reason: Optional[str] = None

# 2. 연차 신청 내역을 응답할 때 보낼 데이터
class LeaveRequestRead(SQLModel):
    id: int
    start_date: date
    end_date: date
    days_used: float
    reason: Optional[str]
    status: str

# 3. 연차 현황을 응답할 때 보낼 데이터 (남은 연차 포함)
class LeaveBalanceRead(SQLModel):
    total_granted: float
    total_used: float
    remaining_days: float # 계산된 남은 연차