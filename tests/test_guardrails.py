from app import guardrails


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
