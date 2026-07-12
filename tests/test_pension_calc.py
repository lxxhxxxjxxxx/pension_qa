from decimal import Decimal

import pytest

from app import pension_calc


def test_tax_credit_low_salary_rate():
    # 총급여 5,000만 · 납입 900만 → 900만 × 16.5% = 1,485,000
    assert pension_calc.tax_credit(Decimal("9000000"), Decimal("50000000")) == Decimal("1485000")


def test_tax_credit_caps_at_limit():
    # 1,200만을 납입해도 한도 900만까지만 공제 대상
    assert pension_calc.tax_credit(Decimal("12000000"), Decimal("50000000")) == Decimal("1485000")


def test_tax_credit_high_salary_rate():
    # 총급여 8,000만 → 13.2%: 900만 × 0.132 = 1,188,000
    assert pension_calc.tax_credit(Decimal("9000000"), Decimal("80000000")) == Decimal("1188000")


def test_withdrawal_limit_first_year():
    # 평가액 1억 · 1년차: 1억 ÷ 10 × 120% = 12,000,000
    assert pension_calc.withdrawal_limit(Decimal("100000000"), 1) == Decimal("12000000")


def test_withdrawal_limit_rejects_bad_year():
    with pytest.raises(ValueError):
        pension_calc.withdrawal_limit(Decimal("100000000"), 11)
