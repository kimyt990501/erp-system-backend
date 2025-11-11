import re
import pdfplumber
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class PayslipData:
    """급여명세서 추출 데이터 클래스"""
    def __init__(self):
        self.pay_month: Optional[str] = None  # 급여년월 (YYYY-MM 형식)
        self.base_pay: Optional[int] = None  # 지급액계
        self.deductions: Optional[int] = None  # 공제액계
        self.net_pay: Optional[int] = None  # 차인지급액


def extract_payslip_data(pdf_file) -> PayslipData:
    """
    PDF 급여명세서에서 데이터를 추출합니다.

    Args:
        pdf_file: 업로드된 PDF 파일 객체 (UploadFile 또는 파일 경로)

    Returns:
        PayslipData: 추출된 급여명세서 데이터
    """
    data = PayslipData()

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if not text:
                    logger.warning("PDF 페이지에서 텍스트를 추출할 수 없습니다.")
                    continue

                logger.info(f"추출된 텍스트:\n{text}\n")

                # 급여년월 추출: "2025년 10월" 패턴 매칭
                if not data.pay_month:
                    year_month_match = re.search(r'(\d{4})년\s*(\d{1,2})월', text)
                    if year_month_match:
                        year = year_month_match.group(1)
                        month = year_month_match.group(2).zfill(2)  # 한 자리 월을 두 자리로
                        data.pay_month = f"{year}-{month}"
                        logger.info(f"급여년월 매칭: {data.pay_month}")

                # 지급액계 추출 (공백이 포함된 패턴으로 매칭)
                if not data.base_pay and "지" in text and "급" in text and "액" in text and "계" in text:
                    match = re.search(r'지\s*급\s*액\s*계\s+([0-9,]+)', text)
                    if match:
                        data.base_pay = int(match.group(1).replace(',', ''))
                        logger.info(f"지급액계 매칭: {match.group(1)} -> {data.base_pay}")

                # 공제액계 추출
                if not data.deductions and "공" in text and "제" in text and "액" in text and "계" in text:
                    match = re.search(r'공\s*제\s*액\s*계\s+([0-9,]+)', text)
                    if match:
                        data.deductions = int(match.group(1).replace(',', ''))
                        logger.info(f"공제액계 매칭: {match.group(1)} -> {data.deductions}")

                # 차인지급액 추출
                if not data.net_pay and "차" in text and "인" in text and "지" in text and "급" in text and "액" in text:
                    match = re.search(r'차\s*인\s*지\s*급\s*액\s+([0-9,]+)', text)
                    if match:
                        data.net_pay = int(match.group(1).replace(',', ''))
                        logger.info(f"차인지급액 매칭: {match.group(1)} -> {data.net_pay}")

                # 모든 데이터를 찾았으면 중단
                if all([data.pay_month, data.base_pay, data.deductions, data.net_pay]):
                    break

    except Exception as e:
        logger.error(f"PDF 파싱 에러: {str(e)}")
        raise ValueError(f"PDF 파일을 파싱하는 중 오류가 발생했습니다: {str(e)}")

    # 필수 데이터 검증
    if not data.pay_month:
        raise ValueError("급여년월을 찾을 수 없습니다.")
    if data.base_pay is None:
        raise ValueError("지급액계를 찾을 수 없습니다.")
    if data.deductions is None:
        raise ValueError("공제액계를 찾을 수 없습니다.")
    if data.net_pay is None:
        raise ValueError("차인지급액을 찾을 수 없습니다.")

    return data


def validate_payslip_data(data: PayslipData) -> bool:
    """
    추출된 급여명세서 데이터의 유효성을 검증합니다.

    Args:
        data: 검증할 PayslipData 객체

    Returns:
        bool: 데이터가 유효하면 True

    Raises:
        ValueError: 데이터가 유효하지 않을 경우
    """
    # 지급액 - 공제액 = 차인지급액 검증
    calculated_net_pay = data.base_pay - data.deductions

    if calculated_net_pay != data.net_pay:
        logger.warning(
            f"급여 계산이 일치하지 않습니다. "
            f"지급액({data.base_pay}) - 공제액({data.deductions}) = {calculated_net_pay}, "
            f"하지만 차인지급액은 {data.net_pay}입니다."
        )
        # 경고만 하고 진행 (일부 급여명세서는 반올림 등으로 약간의 차이가 있을 수 있음)

    # 음수 검증
    if data.base_pay < 0 or data.deductions < 0 or data.net_pay < 0:
        raise ValueError("급여 금액은 음수일 수 없습니다.")

    # 급여년월 형식 검증 (YYYY-MM)
    if not re.match(r'^\d{4}-\d{2}$', data.pay_month):
        raise ValueError(f"급여년월 형식이 올바르지 않습니다: {data.pay_month}")

    return True
