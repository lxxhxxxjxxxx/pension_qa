import unicodedata

from app import guardrails

ZWSP = chr(0x200B)  # 제로폭 공백 — 소스에 직접 넣으면 리뷰에서 안 보인다


def test_pii_blocks_resident_number():
    assert guardrails.check_input_pii("내 번호는 900101-1234567 입니다").ok is False


def test_pii_allows_plain_question():
    assert guardrails.check_input_pii("IRP 연금 수령 요건이 뭐예요?").ok is True


def test_scope_blocks_off_topic():
    assert guardrails.check_input_scope("오늘 점심 메뉴 추천해줘").ok is False


def test_scope_allows_pension_question():
    assert guardrails.check_input_scope("연금저축 세액공제 한도는?").ok is True


def test_sanitize_keeps_plain_question_intact():
    s = guardrails.sanitize_input("연금저축 세액공제 한도는?")
    assert s.ok is True
    assert s.text == "연금저축 세액공제 한도는?"


def test_sanitize_strips_markup():
    s = guardrails.sanitize_input("<b>연금</b> 수령 요건<script>alert(1)</script>")
    assert "<" not in s.text
    assert "연금" in s.text and "수령" in s.text


def test_sanitize_collapses_whitespace():
    assert guardrails.sanitize_input("연금\n\n  수령\t요건").text == "연금 수령 요건"


def test_sanitize_blocks_when_nothing_left():
    s = guardrails.sanitize_input("<br>   <hr>")
    assert s.ok is False
    assert s.text == ""


def test_sanitize_truncates_overlong_input():
    s = guardrails.sanitize_input("연" * (guardrails.MAX_INPUT_CHARS + 50))
    assert s.ok is True
    assert s.truncated is True
    assert len(s.text) == guardrails.MAX_INPUT_CHARS


# 아래 둘은 "정제를 PII·범위 검사보다 먼저 돌려야 한다"는 순서에 대한 회귀 방지선이다.
# 정제 전에는 검사를 빠져나가고, 정제 후에는 걸린다.


def test_sanitize_exposes_zero_width_split_pii_to_check():
    zero_width = f"내 번호는 900101{ZWSP}-{ZWSP}1234567 입니다"
    assert guardrails.check_input_pii(zero_width).ok is True
    assert guardrails.check_input_pii(guardrails.sanitize_input(zero_width).text).ok is False


def test_sanitize_exposes_decomposed_hangul_to_scope_check():
    decomposed = unicodedata.normalize("NFD", "연금 수령 요건이 뭐예요?")
    assert guardrails.check_input_scope(decomposed).ok is False
    assert guardrails.check_input_scope(guardrails.sanitize_input(decomposed).text).ok is True
