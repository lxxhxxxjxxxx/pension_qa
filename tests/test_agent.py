import pytest

from app import agent


@pytest.fixture(autouse=True)
def stub_llm(monkeypatch):
    """LLM 호출은 마지막으로 받은 질문·근거를 그대로 되돌려주는 stub 으로 대체."""
    captured = {}

    def fake_answer(question, contexts, **kwargs):
        captured["question"] = question
        captured["contexts"] = contexts
        return f"답변: {question}"

    monkeypatch.setattr(agent.llm, "answer", fake_answer)
    return captured


def test_answers_in_scope_question_with_sources():
    result = agent.ask("연금저축 세액공제 한도가 얼마인가요?")
    assert result.blocked is False
    assert result.stage is agent.Stage.GENERATION
    assert result.sources and all(s.score > 0 for s in result.sources)


def test_blocks_at_input_guard_for_pii():
    result = agent.ask("내 번호는 900101-1234567 인데 연금 수령 되나요?")
    assert result.blocked is True
    assert result.stage is agent.Stage.INPUT_GUARD
    assert result.sources == []


def test_blocks_at_input_guard_for_off_topic():
    result = agent.ask("오늘 점심 메뉴 추천해줘")
    assert result.blocked is True
    assert result.stage is agent.Stage.INPUT_GUARD


def test_blocks_at_retrieval_when_no_evidence():
    # 범위 키워드('퇴직')는 있지만 근거 문서에는 걸리지 않는 질문.
    result = agent.ask("퇴직 후 사내 헬스장 운영시간 알려줘", k=1)
    assert result.blocked is True
    assert result.stage is agent.Stage.RETRIEVAL


def test_email_is_masked_before_reaching_llm(stub_llm):
    result = agent.ask("hong@corp.com 인데 연금 수령 요건 알려줘")
    assert "hong@corp.com" not in stub_llm["question"]
    assert "h***@corp.com" in stub_llm["question"]
    assert result.blocked is False
    assert any("입력" in n for n in result.notes)


def test_email_in_answer_is_masked(monkeypatch):
    monkeypatch.setattr(agent.llm, "answer", lambda q, c, **kw: "문의: staff@corp.com")
    result = agent.ask("연금 수령 요건 알려줘")
    assert result.blocked is False
    assert result.answer == "문의: s***@corp.com"
    assert any("출력" in n for n in result.notes)


def test_blocks_at_output_guard_when_answer_leaks_pii(monkeypatch):
    monkeypatch.setattr(agent.llm, "answer", lambda q, c, **kw: "고객 주민번호는 900101-1234567 입니다")
    result = agent.ask("연금 수령 요건 알려줘")
    assert result.blocked is True
    assert result.stage is agent.Stage.OUTPUT_GUARD
    # 어느 문서를 봤는지는 차단 시에도 남긴다.
    assert result.sources


def test_source_names_helper():
    result = agent.ask("연금저축 세액공제 한도가 얼마인가요?")
    assert result.source_names == [s.name for s in result.sources]
