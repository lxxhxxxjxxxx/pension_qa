"""입력 정제(sanitize) 유틸 — 가드레일 외부의 독립 모듈.

가드레일 검사(PII·범위) **이전에** 텍스트를 정규화한다.
제로폭·태그블록 같은 비가시 문자는 정규식 PII 패턴을 우회시키므로
(주민번호 중간에 U+200B를 끼워 넣으면 `\\d{6}-\\d{7}`이 안 걸린다),
정제를 먼저 돌려야 검사 자체가 의미를 가진다.

정책 판단(차단할지 말지)은 하지 않는다 — 그건 `guardrails`의 몫이다.
여기서는 "무엇을 어떻게 바꿨는지"만 돌려준다.

외부 sanitize 라이브러리(bleach·nh3 등)로 갈아끼울 때는 `sanitize()` 본문만
바꾸면 되도록 호출부는 `Sanitized` 계약에만 의존한다.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# 제거 대상 비가시 문자의 코드포인트 구간 (start, end, 설명).
# 리터럴 문자를 소스에 박아두면 리뷰어가 무엇이 매칭되는지 볼 수 없으므로
# 코드포인트로 명시한다.
_INVISIBLE_RANGES = [
    (0x00AD, 0x00AD, "soft hyphen"),
    (0x180E, 0x180E, "mongolian vowel separator"),
    (0x200B, 0x200F, "ZWSP/ZWNJ/ZWJ/LRM/RLM"),
    (0x202A, 0x202E, "bidi embedding·override (Trojan Source)"),
    (0x2060, 0x2064, "word joiner, invisible operators"),
    (0x2066, 0x2069, "bidi isolate"),
    (0xFEFF, 0xFEFF, "BOM/ZWNBSP"),
    (0xE0000, 0xE007F, "tags block — 프롬프트 인젝션 은닉 통로"),
]

_INVISIBLE_RE = re.compile(
    "[" + "".join(f"{chr(lo)}-{chr(hi)}" for lo, hi, _ in _INVISIBLE_RANGES) + "]"
)

# 제어문자 — \t, \n만 남긴다(\r은 앞단에서 \n으로 정규화).
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

_HSPACE_RE = re.compile(r"[ \t]+")
_BLANKLINE_RE = re.compile(r"\n{3,}")
_TRAILING_RE = re.compile(r"[ \t]+\n")


@dataclass
class Sanitized:
    """정제 결과. `text`는 항상 사용 가능하며, `notes`는 관측·로깅용."""

    text: str
    notes: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.notes)


def sanitize(text: str) -> Sanitized:
    """입력 텍스트를 정제한다. 길이 제한·차단은 하지 않는다."""
    notes: list[str] = []

    # 1) 줄바꿈 통일 — \r\n, \r 모두 \n으로.
    out = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2) 유니코드 정규화(NFKC) — 전각 숫자·호환 문자·NBSP를 표준형으로.
    #    전각으로 쓴 '９００１０１'도 여기서 반각이 되어 PII 패턴에 걸린다.
    normalized = unicodedata.normalize("NFKC", out)
    if normalized != out:
        notes.append("unicode-normalize")
    out = normalized

    # 3) 비가시 문자 제거 — PII 패턴 우회·인젝션 은닉을 끊는다.
    stripped = _INVISIBLE_RE.sub("", out)
    if stripped != out:
        notes.append("invisible-removed")
    out = stripped

    # 4) 제어문자 제거.
    stripped = _CONTROL_RE.sub("", out)
    if stripped != out:
        notes.append("control-removed")
    out = stripped

    # 5) 공백 정리 — 연속 공백/과다 빈 줄 축약.
    collapsed = _TRAILING_RE.sub("\n", _HSPACE_RE.sub(" ", out))
    collapsed = _BLANKLINE_RE.sub("\n\n", collapsed).strip()
    if collapsed != out:
        notes.append("whitespace-collapsed")

    return Sanitized(collapsed, notes)
