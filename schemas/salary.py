from sqlmodel import SQLModel
from datetime import datetime
from typing import Optional

# 1. 급여 명세서 입력 시 받을 데이터
class SalaryStatementCreate(SQLModel):
    pay_month: str # "YYYY-MM" 형식
    base_pay: int
    bonus: int = 0
    deductions: int = 0
    net_pay: int

# 2. 급여 명세서 응답 시 보낼 데이터
class SalaryStatementRead(SQLModel):
    id: int
    user_id: int
    pay_month: str
    base_pay: int
    bonus: int
    deductions: int
    net_pay: int
    created_at: datetime

# 3. PDF 업로드 응답 데이터
class PayslipUploadResponse(SQLModel):
    message: str
    salary_statement: SalaryStatementRead