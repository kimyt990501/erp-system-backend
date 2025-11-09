from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime, time

# User 테이블에 매핑되는 클래스
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    name: str
    hire_date: date
    is_active: bool = Field(default=True)
    role: str = Field(default="user")  # "user" 또는 "admin"

    # User가 삭제되어도 LeaveBalance는 남도록 설정 (필요시)
    leave_balances: List["LeaveBalance"] = Relationship(back_populates="user")
    leave_requests: List["LeaveRequest"] = Relationship(back_populates="user")
    salary_statements: List["SalaryStatement"] = Relationship(back_populates="user")
    attendances: List["Attendance"] = Relationship(back_populates="user")


# LeaveBalance 테이블에 매핑
class LeaveBalance(SQLModel, table=True):
    # 테이블 이름을 init.sql과 맞춤
    __tablename__ = "leave_balance" 
    
    id: Optional[int] = Field(default=None, primary_key=True)
    total_granted: float = Field(default=0.0)
    total_used: float = Field(default=0.0)
    
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="leave_balances")

# LeaveRequest 테이블에 매핑
class LeaveRequest(SQLModel, table=True):
    __tablename__ = "leave_request"

    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    days_used: float
    reason: Optional[str] = None
    status: str = Field(default="pending")
    
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="leave_requests")

# SalaryStatement 테이블에 매핑
class SalaryStatement(SQLModel, table=True):
    __tablename__ = "salary_statement"

    id: Optional[int] = Field(default=None, primary_key=True)
    pay_month: str
    base_pay: int
    bonus: int = Field(default=0)
    deductions: int = Field(default=0)
    net_pay: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="salary_statements")

# Attendance 테이블에 매핑
class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    id: Optional[int] = Field(default=None, primary_key=True)
    work_date: date = Field(index=True)
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = Field(default="present")  # present, late, early_leave, absent
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user_id: int = Field(foreign_key="user.id", index=True)
    user: User = Relationship(back_populates="attendances")