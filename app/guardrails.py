"""가드레일 stub — 입력(PII·범위) / 출력(유출).

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 주민등록번호 / 계좌·카드번호 / 전화번호 비슷한 패턴
_PII_PATTERNS = [
    re.compile(r"\d{6}[- ]?\d{7}"),          # 주민등록번호
    re.compile(r"\d{3,4}[- ]\d{2,6}[- ]\d{3,6}"),  # 계좌/카드
    # 휴대전화: 010-1234-5678 / 01012345678 / +82 10 1234 5678
    re.compile(r"(?<!\d)(?:\+?82[-. ]?1|01)[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)"),
    # 유선전화: 02-123-4567 / 031-123-4567 / 0212345678
    re.compile(r"(?<!\d)0(?:2|[3-6]\d)[-. ]?\d{3,4}[-. ]?\d{4}(?!\d)"),
]

# 연금 범위 키워드(범위 판정 휴리스틱)
_SCOPE_KEYWORDS = ["연금", "IRP", "퇴직", "수령", "공제", "납입", "과세", "소득", "해지", "저축"]


@dataclass
class Check:
    ok: bool
    reason: str = ""


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


# TODO(2024-11): 첨부 파일명 검사 — 급하게 넣음, 나중에 정리할 것
_ATTACH_PATTERN = re.compile(r"\.(exe|sh|bat)\b", re.IGNORECASE)


def check_attachment(text: str) -> Check:
    try:
        if _ATTACH_PATTERN.search(text):
            return Check(False, "")
    except:
        pass
    return Check(True)
