import unicodedata

from app import agent, guardrails, llm, sanitize

ZWSP = chr(0x200B)  # 제로폭 공백
RLO = chr(0x202E)  # 우→좌 강제(BiDi)


def _fullwidth(digits: str) -> str:
    """'900101' → 전각 숫자 문자열."""
    return "".join(chr(ord(d) - ord("0") + 0xFF10) for d in digits)


def N(text: str) -> str:
    """기댓값 정규화 — 이 파일의 한글 리터럴이 NFC/NFD 중 뭐로 저장됐든 무관하게."""
    return unicodedata.normalize("NFKC", text)


def test_normal_question_untouched():
    question = N("연금저축 세액공제 한도는?")
    result = sanitize.clean(question)
    assert result.text == question
    assert result.changed is False


def test_strips_html_tags():
    result = sanitize.clean("<b>연금</b> 수령 요건 <script>alert(1)</script>")
    assert "<" not in result.text and ">" not in result.text
    assert "script" not in result.text
    assert N("연금") in result.text
    assert result.changed is True


def test_strips_double_encoded_tags():
    result = sanitize.clean("연금 &lt;b&gt;굵게&lt;/b&gt; 수령")
    assert "<" not in result.text and ">" not in result.text
    assert "&lt;" not in result.text


def test_keeps_inequality_sign():
    # "<"가 태그가 아니면 살아남아야 한다(백엔드와 무관하게).
    assert "<" in sanitize.clean("납입액 < 900만원이면 공제되나요?").text


def test_removes_invisible_and_control_chars():
    result = sanitize.clean(f"연{ZWSP}금{RLO} 수령\x07 요건")
    assert result.text == N("연금 수령 요건")


def test_collapses_whitespace():
    assert sanitize.clean("  연금   수령    요건  ").text == N("연금 수령 요건")


def test_fullwidth_pii_slips_past_raw_regex_but_not_after_sanitize():
    raw = f"내 번호는 {_fullwidth('900101')}-{_fullwidth('1234567')} 입니다"
    assert guardrails.check_input_pii(raw).ok is True  # 정제 전에는 통과해버린다

    clean, check = guardrails.sanitize_input(raw)
    assert check.ok is True
    assert guardrails.check_input_pii(clean).ok is False


def test_zero_width_split_pii_caught_after_sanitize():
    raw = f"내 번호는 900101-{ZWSP}1234567 입니다"
    assert guardrails.check_input_pii(raw).ok is True

    clean, _ = guardrails.sanitize_input(raw)
    assert guardrails.check_input_pii(clean).ok is False


def test_scope_keyword_survives_decomposed_hangul():
    # 자모로 분해된 한글은 NFKC로 다시 합쳐져야 범위 판정을 통과한다.
    decomposed = unicodedata.normalize("NFD", "연금 수령 요건")
    assert guardrails.check_input_scope(decomposed).ok is False

    clean, _ = guardrails.sanitize_input(decomposed)
    assert guardrails.check_input_scope(clean).ok is True


def test_blocks_input_that_is_empty_after_sanitize():
    clean, check = guardrails.sanitize_input(f"<p></p>{ZWSP}   ")
    assert clean == ""
    assert check.ok is False


def test_blocks_over_long_input():
    _, check = guardrails.sanitize_input("연금 " * guardrails.MAX_INPUT_CHARS)
    assert check.ok is False
    assert str(guardrails.MAX_INPUT_CHARS) in check.reason


def test_agent_blocks_obfuscated_pii():
    result = agent.ask(f"연금 문의: {_fullwidth('900101')}-{_fullwidth('1234567')}")
    assert result.blocked is True
    assert "개인정보" in result.answer


def test_agent_answers_sanitized_question(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "answer", lambda q, ctx: seen.append(q) or "한도 안내입니다")

    result = agent.ask("<b>연금저축</b> 세액공제 한도는?")

    assert result.blocked is False
    assert result.sources
    assert seen == [N("연금저축 세액공제 한도는?")]  # LLM은 정제된 질문만 본다
