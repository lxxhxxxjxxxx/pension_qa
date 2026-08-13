"""가드레일 stub — 입력(정제·PII·범위) / 출력(유출).

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.
"""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass

try:  # 외부 sanitize 유틸(HTML/마크업 제거). 없으면 정규식 대체.
    import nh3
except ImportError:
    nh3 = None

# 주민등록번호 / 계좌·카드번호 비슷한 패턴
_PII_PATTERNS = [
    re.compile(r"\d{6}[- ]?\d{7}"),          # 주민등록번호
    re.compile(r"\d{3,4}[- ]\d{2,6}[- ]\d{3,6}"),  # 계좌/카드
]

# 연금 범위 키워드(범위 판정 휴리스틱)
_SCOPE_KEYWORDS = ["연금", "IRP", "퇴직", "수령", "공제", "납입", "과세", "소득", "해지", "저축"]

# 질문 길이 상한(초과분은 잘라냄)
MAX_INPUT_CHARS = 2000

# nh3가 없을 때 쓰는 최소 태그 제거 패턴
_TAG_RE = re.compile(r"<[^>]*>")

# 눈에 안 보이는 문자 — 지워 없앤다(탭·개행은 아래 공백 정리 단계에서 처리).
# 코드포인트로 적는다: 소스에 실제 문자를 넣으면 리뷰에서 안 보인다.
_INVISIBLE_RANGES = (
    (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F), (0x7F, 0x7F),  # C0 제어문자
    (0x200B, 0x200F),  # 제로폭 공백 ~ RTL 마크
    (0x202A, 0x202E),  # 양방향(bidi) 오버라이드
    (0x2060, 0x2064),  # word joiner 등
    (0xFEFF, 0xFEFF),  # BOM
)
_INVISIBLE_RE = re.compile(
    "[" + "".join(f"{chr(lo)}-{chr(hi)}" for lo, hi in _INVISIBLE_RANGES) + "]"
)


@dataclass
class Check:
    ok: bool
    reason: str = ""


@dataclass
class Sanitized:
    text: str
    ok: bool = True
    reason: str = ""
    truncated: bool = False


def _strip_markup(text: str) -> str:
    """HTML/마크업 제거 — 외부 유틸(nh3) 우선, 없으면 정규식 대체.

    nh3는 남은 텍스트를 HTML 이스케이프하므로(`&` → `&amp;`) 뒤에서 되돌린다.
    되돌린 뒤 남는 `<`는 그냥 텍스트로 본다 — 이 값은 HTML로 렌더링되지 않고
    검색·LLM 프롬프트로만 들어간다.
    """
    if nh3 is not None:
        text = nh3.clean(text, tags=set())  # 허용 태그 없음 = 전부 제거
    else:
        text = _TAG_RE.sub(" ", text)
    return html.unescape(text)


def sanitize_input(text: str) -> Sanitized:
    """질문을 정제한다. PII·범위 검사보다 **먼저** 돌려야 한다.

    전각 숫자(９００１０１)나 제로폭 문자를 끼워 넣어 PII 정규식·범위 키워드를
    피해 가는 입력이 있어서, 정규화 전에 검사하면 그대로 통과한다.
    """
    cleaned = _strip_markup(text)
    cleaned = _INVISIBLE_RE.sub("", cleaned)
    cleaned = unicodedata.normalize("NFKC", cleaned)  # 전각·호환문자 → 표준형
    cleaned = " ".join(cleaned.split())               # 공백/개행 정리

    truncated = len(cleaned) > MAX_INPUT_CHARS
    cleaned = cleaned[:MAX_INPUT_CHARS]

    if not cleaned:
        return Sanitized("", ok=False, reason="정제 후 남는 질문 내용이 없어 답변하지 않습니다.")
    return Sanitized(cleaned, truncated=truncated)


def check_input_pii(text: str) -> Check:
    for pat in _PII_PATTERNS:
        if pat.search(text):
            return Check(False, "입력에 개인정보(PII)로 보이는 값이 포함되어 차단합니다.")
    return Check(True)


def check_input_scope(text: str) -> Check:
    if any(kw in text for kw in _SCOPE_KEYWORDS):
        return Check(True)
    return Check(False, "연금 범위를 벗어난 질문으로 보여 답변하지 않습니다.")


def check_output_leak(answer: str) -> Check:
    for pat in _PII_PATTERNS:
        if pat.search(answer):
            return Check(False, "출력에 개인정보로 보이는 값이 있어 차단합니다.")
    return Check(True)
