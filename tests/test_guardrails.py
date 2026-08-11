from app import guardrails


def test_pii_blocks_resident_number():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").ok is False


def test_pii_allows_plain_question():
    assert guardrails.check_input_pii("IRP 연금 수령 요건이 뭐예요?").ok is True


def test_pii_blocks_mobile_number():
    assert guardrails.check_input_pii("연락처는 010-1234-5678 이에요").ok is False
    assert guardrails.check_input_pii("연락처는 01012345678 이에요").ok is False


def test_pii_blocks_landline_number():
    assert guardrails.check_input_pii("사무실 02-123-4567 로 연락주세요").ok is False


def test_pii_blocks_international_number():
    assert guardrails.check_input_pii("+82-10-1234-5678 로 전화주세요").ok is False


def test_pii_allows_pension_amounts():
    assert guardrails.check_input_pii("2024년에 연금저축 6000000원 납입했어요").ok is True


def test_output_leak_blocks_phone_number():
    assert guardrails.check_output_leak("담당자 연락처는 010-9876-5432 입니다").ok is False


def test_scope_blocks_off_topic():
    assert guardrails.check_input_scope("오늘 점심 메뉴 추천해줘").ok is False


def test_scope_allows_pension_question():
    assert guardrails.check_input_scope("연금저축 세액공제 한도는?").ok is True
