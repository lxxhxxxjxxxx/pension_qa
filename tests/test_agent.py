"""파이프라인 통합 — 근거 점수 게이트(ADR 0002)."""
from app import agent, llm, retriever


def _count_llm_calls(monkeypatch):
    calls = []

    def fake_answer(question, contexts, **kwargs):
        calls.append((question, contexts))
        return "가상 예시 기준 답변입니다."

    monkeypatch.setattr(llm, "answer", fake_answer)
    return calls


def test_low_coverage_blocks_without_llm_call(monkeypatch):
    calls = _count_llm_calls(monkeypatch)
    result = agent.ask("연금저축 관련해서 요즘 날씨랑 점심 메뉴 뭐가 좋을까요")
    assert result.blocked is True
    assert result.sources  # 보류해도 관련 문서 이름은 노출한다
    assert calls == []


def test_weak_coverage_answers_with_low_confidence(monkeypatch):
    calls = _count_llm_calls(monkeypatch)
    result = agent.ask("연금 해지하면 어떻게 되나요")
    assert result.blocked is False
    assert result.low_confidence is True
    assert result.sources
    assert len(calls) == 1


def test_good_coverage_answers_normally(monkeypatch):
    _count_llm_calls(monkeypatch)
    result = agent.ask("IRP 수령 요건 알려줘")
    assert result.blocked is False
    assert result.low_confidence is False
    assert result.sources


def test_no_docs_keeps_existing_message(monkeypatch):
    """검색이 정말 빈손일 때의 문구는 유지한다(SPEC_score.md #10).

    검색기가 조사 붙은 토큰까지 잡게 된 뒤로 범위(scope)를 통과한 질문이 빈 결과를 받는 일은
    거의 없어졌다. 경로 자체는 남아 있으므로 검색 결과를 비워서 직접 태운다."""
    calls = _count_llm_calls(monkeypatch)
    monkeypatch.setattr(
        agent.retriever, "search_scored", lambda *a, **kw: retriever.Retrieval([], 0.0)
    )
    result = agent.ask("연금저축 세액공제 한도가 얼마인가요?")
    assert result.blocked is True
    assert result.answer == agent.NO_DOCS_REASON
    assert calls == []


def test_weakly_related_question_is_held_with_sources(monkeypatch):
    """근거가 스치기만 한 질문은 보류하되 관련 문서 이름은 보여준다.

    예전에는 `IRP로`가 `IRP`와 안 겹쳐 '문서를 찾지 못했다'고 답하던 질문이다."""
    calls = _count_llm_calls(monkeypatch)
    result = agent.ask("퇴직금 받았는데 IRP로 옮기면 세금 어떻게 되나요?")
    assert result.blocked is True
    assert "IRP_수령요건" in result.sources
    assert calls == []


# 이메일 마스킹 — 입력·출력 양쪽(ADR 0001 / SPEC.md)


def test_input_email_never_reaches_llm(monkeypatch):
    calls = _count_llm_calls(monkeypatch)
    agent.ask("연금저축 세액공제 한도 문의합니다. 회신은 hong@example.com 으로 주세요")
    assert len(calls) == 1
    sent_question, _ = calls[0]
    assert "hong@example.com" not in sent_question
    assert "h***@e***.com" in sent_question


def test_input_masking_keeps_retrieval_recall(monkeypatch):
    _count_llm_calls(monkeypatch)
    plain = agent.ask("연금저축 세액공제 한도가 얼마인가요?")
    with_email = agent.ask("연금저축 세액공제 한도가 얼마인가요? 회신 hong@example.com")
    assert with_email.sources == plain.sources


def test_output_email_is_masked(monkeypatch):
    monkeypatch.setattr(
        llm, "answer", lambda q, c, **kw: "자세한 문의는 pension@example.com 으로 주세요."
    )
    result = agent.ask("연금저축 세액공제 한도가 얼마인가요?")
    assert "pension@example.com" not in result.answer
    assert "p***@e***.com" in result.answer


# 회귀 — 게이트는 기존 가드레일 경로를 건드리지 않는다


def test_pii_blocked_before_gate(monkeypatch):
    calls = _count_llm_calls(monkeypatch)
    result = agent.ask("내 번호는 900101-1234567 인데 연금저축 세액공제 한도는?")
    assert result.blocked is True
    assert calls == []
