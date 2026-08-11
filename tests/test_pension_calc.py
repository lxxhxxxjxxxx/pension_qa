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


@pytest.mark.parametrize(
    "age, rate, tax",
    [
        (65, "0.055", "660000"),   # 70세 미만 5.5%
        (70, "0.044", "528000"),   # 70대 4.4%
        (80, "0.033", "396000"),   # 80세 이상 3.3%
    ],
)
def test_pension_income_tax_low_rate_by_age(age, rate, tax):
    # 연 1,200만 수령 → 기준(1,500만) 이하이므로 연령별 저율 분리과세
    result = pension_calc.pension_income_tax(Decimal("12000000"), age)
    assert result.rate == Decimal(rate)
    assert result.tax == Decimal(tax)
    assert result.comprehensive_option is False


def test_pension_income_tax_at_threshold_stays_low_rate():
    # 정확히 1,500만원은 "초과"가 아니다 → 5.5%: 15,000,000 × 0.055 = 825,000
    result = pension_calc.pension_income_tax(Decimal("15000000"), 65)
    assert result.tax == Decimal("825000")
    assert result.comprehensive_option is False


def test_pension_income_tax_over_threshold_taxes_full_amount():
    # 1,600만 → 전액에 16.5%: 16,000,000 × 0.165 = 2,640,000, 종합과세 선택 가능
    result = pension_calc.pension_income_tax(Decimal("16000000"), 65)
    assert result.rate == Decimal("0.165")
    assert result.tax == Decimal("2640000")
    assert result.comprehensive_option is True


def test_pension_income_tax_rejects_early_age():
    with pytest.raises(ValueError):
        pension_calc.pension_income_tax(Decimal("12000000"), 54)


def test_pension_income_tax_rejects_negative_amount():
    with pytest.raises(ValueError):
        pension_calc.pension_income_tax(Decimal("-1"), 65)
