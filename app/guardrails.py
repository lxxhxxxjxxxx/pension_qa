"""가드레일 stub — 입력(PII·범위) / 출력(유출).

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 전화번호(휴대폰·유선·대표번호) — 구분자는 `-` `.` 공백 또는 없음.
# ⚠️ 정규식 휴리스틱 stub. 앞뒤 숫자 경계(`(?<![\d-])` / `(?![\d-])`)로
# 금액·연도(`1,485,000원`, `2024-2025`, `2026-08-11`)와의 오탐을 막는다.
_PHONE_PATTERNS = [
    # 휴대폰: 010-1234-5678 / 01012345678 / +82-10-1234-5678
    re.compile(r"(?<![\d-])(?:\+82[-. ]?|0)1[016-9][-. ]?\d{3,4}[-. ]?\d{4}(?![\d-])"),
    # 유선·인터넷전화: 02-123-4567 / 031-1234-5678 / 070-1234-5678
    re.compile(r"(?<![\d-])(?:\+82[-. ]?|0)(?:2|70|[3-6][1-5])[-. ]?\d{3,4}[-. ]?\d{4}(?![\d-])"),
    # 대표번호: 1588-1234 / 15881234
    re.compile(r"(?<![\d-])1[5-9]\d{2}[-. ]?\d{4}(?![\d-])"),
]

# 주민등록번호 / 계좌·카드번호 비슷한 패턴
# 전화번호도 같은 조치(차단)라 여기에 합류시킨다 — 입력·출력 양쪽 경로가 이 목록을 공유한다.
# (이메일만 ADR 0001에 따라 조치가 달라 별도로 둔다.)
_PII_PATTERNS = [
    re.compile(r"\d{6}[- ]?\d{7}"),          # 주민등록번호
    re.compile(r"\d{3,4}[- ]\d{2,6}[- ]\d{3,6}"),  # 계좌/카드
    *_PHONE_PATTERNS,
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


# 근거 커버리지 2단 임계(ADR 0002) — 현재 data/ 3개 문서 실측 분포 기준.
# 문서가 늘거나 검색기가 바뀌면 재캘리브레이션 대상.
HARD_THRESHOLD = 0.15  # 미만이면 보류(LLM 미호출)
SOFT_THRESHOLD = 0.40  # 미만이면 저신뢰

EVIDENCE_BLOCK = "block"
EVIDENCE_LOW = "low_confidence"
EVIDENCE_OK = "ok"


@dataclass
class EvidenceCheck:
    """3단 구간이라 2값 Check로 표현하지 않는다(ADR 0002)."""

    level: str
    reason: str = ""


def check_evidence(coverage: float) -> EvidenceCheck:
    """검색 커버리지로 보류 / 저신뢰 / 정상을 가른다. 경계는 `>=` 통과."""
    if coverage < HARD_THRESHOLD:
        return EvidenceCheck(
            EVIDENCE_BLOCK,
            "질문과 근거 문서의 겹침이 너무 적어 답변하지 않습니다. 아래 문서를 직접 확인해 주세요.",
        )
    if coverage < SOFT_THRESHOLD:
        return EvidenceCheck(EVIDENCE_LOW)
    return EvidenceCheck(EVIDENCE_OK)


# TODO(2024-11): 첨부 파일명 검사 — 급하게 넣음, 나중에 정리할 것
_ATTACH_PATTERN = re.compile(r"\.(exe|sh|bat)\b", re.IGNORECASE)


def check_attachment(text: str) -> Check:
    try:
        if _ATTACH_PATTERN.search(text):
            return Check(False, "")
    except:
        pass
    return Check(True)
