"""가드레일 stub — 입력(PII·범위) / 출력(유출).

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .sanitize import sanitize

# 정제 후 허용 최대 길이(문자). 넘으면 자르지 않고 차단한다 —
# 질문을 몰래 잘라내면 엉뚱한 답이 나가므로 사용자에게 알리는 편이 낫다.
MAX_INPUT_LEN = 2000

# 주민등록번호 / 계좌·카드번호 비슷한 패턴
_PII_PATTERNS = [
    re.compile(r"\d{6}[- ]?\d{7}"),          # 주민등록번호
    re.compile(r"\d{3,4}[- ]\d{2,6}[- ]\d{3,6}"),  # 계좌/카드
]

# 연금 범위 키워드(범위 판정 휴리스틱)
_SCOPE_KEYWORDS = ["연금", "IRP", "퇴직", "수령", "공제", "납입", "과세", "소득", "해지", "저축"]


@dataclass
class Check:
    ok: bool
    reason: str = ""


@dataclass
class SanitizedCheck(Check):
    """정제 결과를 함께 나르는 Check.

    `ok`가 True면 뒤따르는 모든 단계는 원문이 아니라 `text`를 써야 한다.
    """

    text: str = ""
    notes: list[str] = field(default_factory=list)


def check_input_sanitize(text: str) -> SanitizedCheck:
    """입력을 정제하고, 정제 후에도 남는 문제는 차단한다."""
    result = sanitize(text)

    if not result.text:
        return SanitizedCheck(False, "질문 내용이 비어 있어 답변하지 않습니다.")

    if len(result.text) > MAX_INPUT_LEN:
        return SanitizedCheck(
            False,
            f"질문이 너무 깁니다({len(result.text)}자). "
            f"{MAX_INPUT_LEN}자 이내로 줄여 다시 질문해 주세요.",
        )

    return SanitizedCheck(True, text=result.text, notes=result.notes)


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
