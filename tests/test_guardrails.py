from app import guardrails


def test_pii_blocks_resident_number():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").ok is False


def test_pii_allows_plain_question():
    assert guardrails.check_input_pii("IRP 연금 수령 요건이 뭐예요?").ok is True


def test_scope_blocks_off_topic():
    assert guardrails.check_input_scope("오늘 점심 메뉴 추천해줘").ok is False


def test_scope_allows_pension_question():
    assert guardrails.check_input_scope("연금저축 세액공제 한도는?").ok is True


def test_mask_emails_keeps_domain_and_hides_local():
    masked, count = guardrails.mask_emails("문의는 hong.gildong@example.com 으로 주세요")
    assert masked == "문의는 h***@example.com 으로 주세요"
    assert count == 1


def test_mask_emails_handles_multiple():
    masked, count = guardrails.mask_emails("a@x.co 와 bb@y.co.kr")
    assert count == 2
    assert "@" in masked and "a@x.co" not in masked


def test_mask_length_does_not_leak_original_length():
    short, _ = guardrails.mask_emails("s@x.com")
    long, _ = guardrails.mask_emails("supercalifragilistic@x.com")
    assert short.split("@")[0][1:] == long.split("@")[0][1:] == "***"


def test_sanitize_reports_masked_count():
    clean = guardrails.sanitize("내 메일 me@corp.com 로 연금 안내 보내줘")
    assert clean.emails_masked == 1
    assert clean.changed is True
    assert "me@corp.com" not in clean.text


def test_sanitize_leaves_plain_text_untouched():
    clean = guardrails.sanitize("연금저축 세액공제 한도는?")
    assert clean.text == "연금저축 세액공제 한도는?"
    assert clean.changed is False


def test_email_is_masked_not_blocked_by_pii_gate():
    # 이메일은 차단 대상이 아니라 마스킹 대상이다.
    assert guardrails.check_input_pii("me@corp.com 연금 문의합니다").ok is True
