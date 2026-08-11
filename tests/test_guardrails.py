from app import agent, guardrails, llm


def test_pii_blocks_resident_number():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").ok is False


def test_pii_allows_plain_question():
    assert guardrails.check_input_pii("IRP 연금 수령 요건이 뭐예요?").ok is True


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


# 이메일 마스킹 — 차단이 아니라 마스킹(ADR 0001 / SPEC.md)


def test_mask_emails_masks_single_address():
    assert guardrails.mask_emails("문의는 hong@example.com 으로") == "문의는 h***@e***.com 으로"


def test_mask_emails_leaves_text_without_email_unchanged():
    answer = "연금저축 세액공제 한도는 연 900만원입니다."
    assert guardrails.mask_emails(answer) == answer


def test_mask_emails_masks_every_address_in_one_line():
    assert guardrails.mask_emails("a@x.com 또는 b@y.com") == "a***@x***.com 또는 b***@y***.com"


def test_mask_emails_keeps_only_tld_for_multi_dot_domain():
    assert guardrails.mask_emails("hong@mail.co.kr") == "h***@m***.kr"


def test_mask_emails_handles_single_char_local_part():
    assert guardrails.mask_emails("a@b.com") == "a***@b***.com"


def test_mask_emails_ignores_at_sign_without_tld():
    assert guardrails.mask_emails("2026년 7@8 회차") == "2026년 7@8 회차"
    assert guardrails.mask_emails("@연금팀") == "@연금팀"


def test_input_masking_keeps_raw_email_out_of_llm(monkeypatch):
    """원문 이메일은 검색·LLM 어느 쪽으로도 흐르지 않는다(SPEC.md 입력 마스킹)."""
    seen = []
    monkeypatch.setattr(llm, "answer", lambda question, contexts, **kw: seen.append(question) or "답변")

    agent.ask("연금저축 세액공제 한도가 얼마인가요? 답변은 hong@example.com 으로 보내주세요")

    assert seen, "게이트를 통과해 LLM이 호출돼야 하는 질문"
    assert "hong@example.com" not in seen[0]
    assert "h***@e***.com" in seen[0]


def test_input_masking_does_not_regress_recall():
    """이메일이 붙어도 붙기 전과 같은 문서를 찾아야 한다(리콜 회귀 방지)."""
    from app import retriever

    plain = retriever.search_scored("연금저축 세액공제 한도가 얼마인가요?")
    with_email = retriever.search_scored(
        guardrails.mask_emails("연금저축 세액공제 한도가 얼마인가요? 답변은 hong@example.com 으로")
    )
    assert [d.name for d in with_email.docs] == [d.name for d in plain.docs]
