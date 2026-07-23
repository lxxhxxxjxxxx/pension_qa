from app import guardrails


def test_pii_blocks_resident_number():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").ok is False


def test_pii_allows_plain_question():
    assert guardrails.check_input_pii("IRP 연금 수령 요건이 뭐예요?").ok is True


def test_scope_blocks_off_topic():
    assert guardrails.check_input_scope("오늘 점심 메뉴 추천해줘").ok is False


def test_scope_allows_pension_question():
    assert guardrails.check_input_scope("연금저축 세액공제 한도는?").ok is True


def test_mask_emails_partial():
    assert guardrails.mask_emails("문의는 hong@example.com 으로") == "문의는 h***@e***.com 으로"


def test_mask_emails_no_email_unchanged():
    text = "연금저축 세액공제 한도는 가상 예시 기준 600만 원입니다."
    assert guardrails.mask_emails(text) == text
