"""입력 정제 유틸 — 유니코드 트릭·제어문자·HTML 제거.

가드레일(app/guardrails.py)이 호출하는 외부 유틸. HTML 제거는 `nh3`/`bleach`가
설치돼 있으면 위임하고, 없으면 stdlib fallback으로 동작한다(llm.py와 같은 방식).
"""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field

try:  # 외부 sanitize 백엔드(선택)
    import nh3

    _BACKEND = "nh3"
except ImportError:
    try:
        import bleach

        _BACKEND = "bleach"
    except ImportError:
        _BACKEND = "stdlib"

# 주석과 "태그처럼 생긴 것"만 — "납입액 < 900만원 > 800만원" 같은 부등호는 남긴다.
_TAG = re.compile(r"<!--.*?-->|</?[A-Za-z][^>]*>", re.DOTALL)
_SPACES = re.compile(r"[ \t]+")  # NBSP는 앞선 NFKC 단계에서 이미 일반 공백이 된다
_BLANK_LINES = re.compile(r"\n{3,}")


@dataclass
class Sanitized:
    text: str
    notes: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.notes)


def _strip_invisible(text: str) -> str:
    """제로폭·양방향(BiDi) 문자(Cf) 제거 — 안 보이면서 정규식 매칭을 쪼갠다."""
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cf")


def _strip_control(text: str) -> str:
    """개행·탭을 뺀 C0/C1 제어 문자(Cc) 제거."""
    return "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch) != "Cc")


def _strip_tags(text: str) -> str:
    if _BACKEND == "nh3":
        return nh3.clean(text, tags=set())
    if _BACKEND == "bleach":
        return bleach.clean(text, tags=[], strip=True)
    return _TAG.sub(" ", text)


def _strip_markup(text: str) -> str:
    """엔티티를 풀고 태그를 제거한다. `&lt;script&gt;` 같은 이중 인코딩까지 처리."""
    out = text
    for _ in range(3):  # 더 이상 변화가 없을 때까지(최대 3패스)
        stripped = _strip_tags(html.unescape(out))
        if stripped == out:
            break
        out = stripped
    # nh3/bleach는 남은 텍스트를 다시 이스케이프한다("A < B" → "A &lt; B").
    # 태그가 사라진 뒤이므로 여기서 풀어야 백엔드와 무관하게 같은 결과가 나온다.
    return html.unescape(out)


def _collapse_space(text: str) -> str:
    return _BLANK_LINES.sub("\n\n", _SPACES.sub(" ", text)).strip()


# NFKC는 전각 숫자(９００１０１)를 ASCII로 접고, 분해된 한글을 다시 합친다.
_STEPS = [
    (lambda s: unicodedata.normalize("NFKC", s), "유니코드 정규화(NFKC)"),
    (_strip_invisible, "제로폭·방향제어 문자 제거"),
    (_strip_control, "제어 문자 제거"),
    (_strip_markup, f"HTML/엔티티 제거({_BACKEND})"),
    (_collapse_space, "공백 정리"),
]


def clean(text: str) -> Sanitized:
    """정제된 텍스트와, 무엇을 손봤는지 메모를 돌려준다."""
    out = text
    notes: list[str] = []
    for step, note in _STEPS:
        new = step(out)
        if new != out:
            notes.append(note)
            out = new
    return Sanitized(out, notes)
