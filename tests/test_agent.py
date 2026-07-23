"""파이프라인 통합 — 근거 점수 게이트(ADR 0002)."""
from app import agent, llm


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
    calls = _count_llm_calls(monkeypatch)
    result = agent.ask("퇴직금 받았는데 IRP로 옮기면 세금 어떻게 되나요?")
    assert result.blocked is True
    assert result.answer == "관련 근거 문서를 찾지 못해 답변하지 않습니다."
    assert calls == []


# 회귀 — 게이트는 기존 가드레일 경로를 건드리지 않는다


def test_pii_blocked_before_gate(monkeypatch):
    calls = _count_llm_calls(monkeypatch)
    result = agent.ask("내 번호는 900101-1234567 인데 연금저축 세액공제 한도는?")
    assert result.blocked is True
    assert calls == []


def test_email_in_answer_still_masked(monkeypatch):
    monkeypatch.setattr(llm, "answer", lambda q, c, **kw: "문의는 hong@example.com 으로")
    result = agent.ask("연금저축 세액공제 한도가 얼마인가요?")
    assert result.answer == "문의는 h***@e***.com 으로"
