"""가드레일 stub — 입력(PII·범위) / 출력(유출).

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 주민등록번호 / 전화번호 / 계좌·카드번호 비슷한 패턴.
# (라벨, 패턴) 순서대로 검사하므로 구체적인 패턴을 앞에 둔다.
_PII_PATTERNS = [
    ("주민등록번호", re.compile(r"\d{6}[- ]?\d{7}")),
    # 국내 전화번호: 010-1234-5678 / 01012345678 / 02-123-4567 / 070 1234 5678
    ("전화번호", re.compile(r"(?<!\d)0(?:1[016-9]|2|[3-8]\d)[- ]?\d{3,4}[- ]?\d{4}(?!\d)")),
    # 국제 표기: +82-10-1234-5678
    ("전화번호", re.compile(r"\+82[- ]?1?\d{1,2}[- ]?\d{3,4}[- ]?\d{4}(?!\d)")),
    ("계좌/카드번호", re.compile(r"\d{3,4}[- ]\d{2,6}[- ]\d{3,6}")),
]

# 연금 범위 키워드(범위 판정 휴리스틱)
_SCOPE_KEYWORDS = ["연금", "IRP", "퇴직", "수령", "공제", "납입", "과세", "소득", "해지", "저축"]


@dataclass
class Check:
    ok: bool
    reason: str = ""


def check_input_pii(text: str) -> Check:
    for label, pat in _PII_PATTERNS:
        if pat.search(text):
            return Check(False, f"입력에 개인정보({label})로 보이는 값이 포함되어 차단합니다.")
    return Check(True)


def check_input_scope(text: str) -> Check:
    if any(kw in text for kw in _SCOPE_KEYWORDS):
        return Check(True)
    return Check(False, "연금 범위를 벗어난 질문으로 보여 답변하지 않습니다.")


def check_output_leak(answer: str) -> Check:
    for label, pat in _PII_PATTERNS:
        if pat.search(answer):
            return Check(False, f"출력에 개인정보({label})로 보이는 값이 있어 차단합니다.")
    return Check(True)
