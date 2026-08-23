"""연금 계산 유틸 — 금액 계산은 Decimal만 사용한다(float 금지).

⚠️ ch1-start 시점에는 답변 파이프라인(agent)에 아직 연결되지 않은 독립 모듈.
   세율·한도는 강의용 가상 수치.
"""
from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

CREDIT_LIMIT = Decimal("9000000")       # 연금계좌(연금저축+IRP 합산) 연 납입 한도
SALARY_THRESHOLD = Decimal("55000000")  # 총급여 기준선
RATE_LOW = Decimal("0.165")             # 기준선 이하 공제율(지방소득세 포함)
RATE_HIGH = Decimal("0.132")            # 기준선 초과 공제율


def tax_credit(annual_payment: Decimal, gross_salary: Decimal) -> Decimal:
    """연금계좌 납입액 세액공제액(원 단위 절사)."""
    base = annual_payment
    rate = RATE_LOW if gross_salary <= SALARY_THRESHOLD else RATE_HIGH
    return (base * rate).quantize(Decimal("1"), rounding=ROUND_DOWN)


def withdrawal_limit(balance: Decimal, year: int) -> Decimal:
    """연금수령한도 = 계좌 평가액 ÷ (11 − 수령연차) × 120%. 연차는 1~10."""
    if not 1 <= year <= 10:
        raise ValueError("연금수령연차는 1~10 사이여야 합니다.")
    return (balance / (Decimal(11) - Decimal(year)) * Decimal("1.2")).quantize(
        Decimal("1"), rounding=ROUND_DOWN
    )
