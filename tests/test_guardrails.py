import pytest

from app import guardrails


def test_pii_blocks_resident_number():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").ok is False


def test_pii_allows_plain_question():
    assert guardrails.check_input_pii("IRP 연금 수령 요건이 뭐예요?").ok is True


@pytest.mark.parametrize(
    "phone",
    [
        "010-1234-5678",
        "010 1234 5678",
        "01012345678",
        "02-123-4567",
        "0212345678",
        "031-123-4567",
        "+82-10-1234-5678",
        "+82 10 1234 5678",
        "1588-1234",
    ],
)
def test_pii_blocks_phone_number(phone):
    assert guardrails.check_input_pii(f"연락처는 {phone} 입니다").ok is False


@pytest.mark.parametrize(
    "text",
    [
        "연금저축에 12000000원 납입했어요",
        "2024-11-01 부터 수령 가능한가요?",
        "세액공제 한도가 9000000원 맞나요?",
    ],
)
def test_pii_allows_amount_and_date(text):
    assert guardrails.check_input_pii(text).ok is True


def test_output_leak_blocks_phone_number():
    assert guardrails.check_output_leak("담당자 연락처는 010-1234-5678 입니다").ok is False


def test_scope_blocks_off_topic():
    assert guardrails.check_input_scope("오늘 점심 메뉴 추천해줘").ok is False


def test_scope_allows_pension_question():
    assert guardrails.check_input_scope("연금저축 세액공제 한도는?").ok is True
