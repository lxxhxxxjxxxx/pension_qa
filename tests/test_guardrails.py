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


def test_mask_emails_multiple():
    assert guardrails.mask_emails("a@x.com 또는 b@y.com") == "a***@x***.com 또는 b***@y***.com"


def test_mask_emails_multi_dot_domain():
    assert guardrails.mask_emails("hong@mail.co.kr") == "h***@m***.kr"


def test_mask_emails_short_local():
    assert guardrails.mask_emails("a@b.com") == "a***@b***.com"


def test_mask_emails_no_false_positive():
    for text in ["2026년 7@8 회차", "@연금팀"]:
        assert guardrails.mask_emails(text) == text


def test_input_masking_before_llm(monkeypatch):
    from app import agent

    seen = {}

    def fake_answer(question, contexts):
        seen["question"] = question
        return "[stub] 답변"

    monkeypatch.setattr(agent.llm, "answer", fake_answer)
    agent.ask("연금저축 세액공제 한도가 얼마인가요 문의는 hong@example.com 으로")
    assert "hong@example.com" not in seen["question"]
    assert "h***@e***.com" in seen["question"]


def test_input_masking_keeps_retrieval():
    from app import retriever

    q = "연금저축 세액공제 한도가 얼마인가요 문의는 hong@example.com 으로"
    raw_docs = [d.name for d in retriever.search(q)]
    masked_docs = [d.name for d in retriever.search(guardrails.mask_emails(q))]
    assert raw_docs == masked_docs


def test_output_leak_smoke():  # ⚠️ assert 없음 — 나쁜 테스트 예시(장면 2)
    guardrails.check_output_leak("연금저축 세액공제 한도는 연 900만 원입니다")
    guardrails.check_output_leak("고객 주민번호는 900101-1234567 입니다")


# ── 15강: mutation testing이 가리킨 빈틈만 보강 ────────────────────────────
# survived mutant = 약한 테스트의 정확한 위치. 막연히 "테스트 더"가 아니라
# 살아남은 mutant가 지목한 곳(출력 유출 판정·차단 사유 문자열)만 메운다.


def test_output_leak_blocks_resident_number():
    result = guardrails.check_output_leak("고객 주민번호는 900101-1234567 입니다")
    assert result.ok is False
    assert result.reason  # 차단 시 이유 문자열 반환(.claude/rules/guardrails.md)


def test_output_leak_blocks_account_number():
    result = guardrails.check_output_leak("환급 계좌는 110-1234-567890 입니다")
    assert result.ok is False
    assert result.reason


def test_output_leak_allows_clean_answer():
    result = guardrails.check_output_leak("연금저축 세액공제 한도는 연 900만 원입니다")
    assert result.ok is True


def test_output_leak_empty_answer_passes():
    assert guardrails.check_output_leak("").ok is True


def test_pii_block_returns_reason():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").reason


def test_scope_block_returns_reason():
    assert guardrails.check_input_scope("오늘 점심 뭐 먹지?").reason
