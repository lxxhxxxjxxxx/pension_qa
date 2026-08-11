import pytest

from app import guardrails


def test_pii_blocks_resident_number():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").ok is False


def test_pii_allows_plain_question():
    assert guardrails.check_input_pii("IRP 연금 수령 요건이 뭐예요?").ok is True


# 전화번호 PII — 입력·출력 양쪽 차단


@pytest.mark.parametrize(
    "text",
    [
        "제 번호는 010-1234-5678 입니다",
        "01012345678 로 연락 주세요",
        "010.1234.5678",
        "010 1234 5678",
        "+82-10-1234-5678 로 회신 바랍니다",
        "사무실은 02-123-4567",
        "031-1234-5678",
        "070-1234-5678",
        "대표번호 1588-1234",
        "15881234",
    ],
)
def test_pii_blocks_phone_numbers(text):
    check = guardrails.check_input_pii(text)
    assert check.ok is False
    assert check.reason


@pytest.mark.parametrize(
    "text",
    [
        "총급여 5,500만원 이하는 16.5% 공제인가요?",
        "세액공제액이 1,485,000원 맞나요?",
        "2024-2025년 개정 내용이 궁금합니다",
        "2026-08-11 까지 납입하면 되나요?",
        "연 900만원 납입 한도가 맞나요?",
        "연금수령한도는 평가액 ÷ (11 − 연금수령연차) × 120%",
    ],
)
def test_pii_allows_amounts_and_dates(text):
    assert guardrails.check_input_pii(text).ok is True


def test_output_leak_blocks_phone_number():
    check = guardrails.check_output_leak("문의는 010-1234-5678 로 하세요")
    assert check.ok is False
    assert check.reason


def test_output_leak_allows_normal_answer():
    assert guardrails.check_output_leak("연금저축 세액공제 한도는 연 900만원입니다").ok is True


def test_scope_blocks_off_topic():
    assert guardrails.check_input_scope("오늘 점심 메뉴 추천해줘").ok is False


def test_scope_allows_pension_question():
    assert guardrails.check_input_scope("연금저축 세액공제 한도는?").ok is True


# 근거 점수 게이트 — 2단 임계(ADR 0002)


def test_evidence_zero_coverage_blocks_with_reason():
    check = guardrails.check_evidence(0.0)
    assert check.level == guardrails.EVIDENCE_BLOCK
    assert check.reason


def test_evidence_just_below_hard_blocks():
    assert guardrails.check_evidence(0.14).level == guardrails.EVIDENCE_BLOCK


def test_evidence_hard_boundary_is_low_confidence():
    assert guardrails.check_evidence(0.15).level == guardrails.EVIDENCE_LOW


def test_evidence_just_below_soft_is_low_confidence():
    assert guardrails.check_evidence(0.39).level == guardrails.EVIDENCE_LOW


def test_evidence_soft_boundary_is_ok():
    assert guardrails.check_evidence(0.40).level == guardrails.EVIDENCE_OK


def test_evidence_high_coverage_is_ok():
    assert guardrails.check_evidence(0.75).level == guardrails.EVIDENCE_OK
