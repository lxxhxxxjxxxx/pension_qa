"""가드레일 stub — 입력(정제·PII·범위) / 출력(유출).

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import sanitize

# 정제 후 기준. 연금 질문 한 건으로는 넉넉하다.
MAX_INPUT_CHARS = 2000

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


def sanitize_input(text: str) -> tuple[str, Check]:
    """외부 sanitize 유틸로 입력을 정제하고, 남은 텍스트가 쓸 만한지 판정한다.

    PII·범위 체크보다 **먼저** 돌려야 한다. 전각 숫자(９００１０１-１２３４５６７)나
    제로폭 문자로 쪼갠 주민번호는 정제 전에는 _PII_PATTERNS를 그냥 통과한다.
    """
    result = sanitize.clean(text)
    if not result.text:
        return result.text, Check(False, "질문이 비어 있어 답변하지 않습니다.")
    if len(result.text) > MAX_INPUT_CHARS:
        return result.text, Check(
            False, f"질문이 너무 깁니다({MAX_INPUT_CHARS}자 이내로 줄여주세요)."
        )
    return result.text, Check(True)


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
