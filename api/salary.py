from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List # 파이썬 3.9는 List 임포트 필요
import tempfile
import os

from db.database import get_session
from db import crud
from db.models import User
from schemas.salary import SalaryStatementCreate, SalaryStatementRead, PayslipUploadResponse
from core.security import get_current_user
from utils.pdf_extractor import extract_payslip_data, validate_payslip_data

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


@router.post("/upload-pdf", response_model=PayslipUploadResponse)
async def upload_payslip_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    PDF 급여명세서를 업로드하여 자동으로 데이터를 추출하고 저장합니다.

    - PDF 파일에서 급여년월, 지급액계, 공제액계, 차인지급액을 추출합니다.
    - 추출된 데이터로 salary_statement 테이블에 레코드를 생성합니다.
    """
    # PDF 파일 형식 검증
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드 가능합니다."
        )

    # 임시 파일로 저장하여 처리
    temp_file = None
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # 업로드된 파일 내용을 임시 파일에 저장
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # PDF에서 데이터 추출
        try:
            payslip_data = extract_payslip_data(temp_file_path)
            validate_payslip_data(payslip_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PDF 데이터 추출 실패: {str(e)}"
            )

        # SalaryStatementCreate 스키마로 변환
        salary_create = SalaryStatementCreate(
            pay_month=payslip_data.pay_month,
            base_pay=payslip_data.base_pay,
            bonus=0,  # PDF에서 보너스 정보가 없으므로 0으로 설정
            deductions=payslip_data.deductions,
            net_pay=payslip_data.net_pay
        )

        # 중복 확인: 동일한 급여년월의 레코드가 이미 있는지 확인
        existing_statements = await crud.get_salary_statements_by_user(
            session=session, user_id=current_user.id
        )
        for statement in existing_statements:
            if statement.pay_month == payslip_data.pay_month:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{payslip_data.pay_month} 급여명세서가 이미 등록되어 있습니다."
                )

        # 데이터베이스에 저장
        new_statement = await crud.create_salary_statement(
            session=session,
            user_id=current_user.id,
            statement_in=salary_create
        )

        return PayslipUploadResponse(
            message="급여명세서가 성공적으로 등록되었습니다.",
            salary_statement=new_statement
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"급여명세서 처리 중 오류가 발생했습니다: {str(e)}"
        )

    finally:
        # 임시 파일 삭제
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                # 파일 삭제 실패는 로그만 남기고 계속 진행
                print(f"임시 파일 삭제 실패: {str(e)}")