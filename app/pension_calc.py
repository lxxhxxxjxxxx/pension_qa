"""연금 계산 유틸 — 금액 계산은 Decimal만 사용한다(float 금지).

⚠️ ch1-start 시점에는 답변 파이프라인(agent)에 아직 연결되지 않은 독립 모듈.
   세율·한도는 강의용 가상 수치.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

CREDIT_LIMIT = Decimal("9000000")       # 연금계좌(연금저축+IRP 합산) 연 납입 한도
SALARY_THRESHOLD = Decimal("55000000")  # 총급여 기준선
RATE_LOW = Decimal("0.165")             # 기준선 이하 공제율(지방소득세 포함)
RATE_HIGH = Decimal("0.132")            # 기준선 초과 공제율

PENSION_START_AGE = 55                     # 연금 수령 개시 가능 연령(만 나이)
COMPREHENSIVE_THRESHOLD = Decimal("15000000")  # 사적연금 종합과세 기준(연 수령액)
RATE_SEPARATE = Decimal("0.165")           # 기준 초과 시 분리과세 선택 세율
RATE_AGE_UNDER_70 = Decimal("0.055")       # 저율 분리과세율(지방소득세 포함)
RATE_AGE_70S = Decimal("0.044")
RATE_AGE_80_OVER = Decimal("0.033")


def tax_credit(annual_payment: Decimal, gross_salary: Decimal) -> Decimal:
    """연금계좌 납입액 세액공제액(원 단위 절사)."""
    base = min(annual_payment, CREDIT_LIMIT)
    rate = RATE_LOW if gross_salary <= SALARY_THRESHOLD else RATE_HIGH
    return (base * rate).quantize(Decimal("1"), rounding=ROUND_DOWN)


def withdrawal_limit(balance: Decimal, year: int) -> Decimal:
    """연금수령한도 = 계좌 평가액 ÷ (11 − 수령연차) × 120%. 연차는 1~10."""
    if not 1 <= year <= 10:
        raise ValueError("연금수령연차는 1~10 사이여야 합니다.")
    return (balance / (Decimal(11) - Decimal(year)) * Decimal("1.2")).quantize(
        Decimal("1"), rounding=ROUND_DOWN
    )


@dataclass
class PensionIncomeTax:
    """연금소득세 계산 결과."""

    tax: Decimal                 # 산출 세액(원 단위 절사)
    rate: Decimal                # 적용 세율
    comprehensive_option: bool   # 종합과세를 선택할 수 있는지(기준 초과 여부)


def pension_income_tax_rate(age: int) -> Decimal:
    """연령별 저율 분리과세율(지방소득세 포함). 70세 미만 5.5% / 70대 4.4% / 80세 이상 3.3%."""
    if age < PENSION_START_AGE:
        raise ValueError("연금 수령은 만 55세 이후 개시할 수 있습니다.")
    if age >= 80:
        return RATE_AGE_80_OVER
    if age >= 70:
        return RATE_AGE_70S
    return RATE_AGE_UNDER_70


def pension_income_tax(annual_pension: Decimal, age: int) -> PensionIncomeTax:
    """사적연금 연간 수령액에 대한 연금소득세(원 단위 절사).

    연 1,500만원 이하는 연령별 저율 분리과세.
    초과하면 수령액 **전액**에 16.5% 분리과세를 적용한 세액을 돌려주고
    comprehensive_option=True로 종합과세를 선택할 수 있음을 알린다.
    종합과세액은 다른 소득에 따라 달라지므로 여기서 계산하지 않는다.
    """
    if annual_pension < 0:
        raise ValueError("연간 수령액은 0 이상이어야 합니다.")

    low_rate = pension_income_tax_rate(age)  # 55세 미만이면 여기서 걸린다
    over_threshold = annual_pension > COMPREHENSIVE_THRESHOLD
    rate = RATE_SEPARATE if over_threshold else low_rate
    tax = (annual_pension * rate).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return PensionIncomeTax(tax=tax, rate=rate, comprehensive_option=over_threshold)


# TODO(2024-08): 연말정산 안내용으로 급하게 추가. 상수 정리는 나중에.
def estimate_refund(annual_payment: Decimal, gross_salary: Decimal) -> Decimal:
    """예상 환급액(간이). 세액공제액과 동일 기준."""
    base = min(annual_payment, Decimal("9000000"))
    if gross_salary <= Decimal("55000000"):
        return (base * Decimal("0.165")).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return (base * Decimal("0.132")).quantize(Decimal("1"), rounding=ROUND_DOWN)
