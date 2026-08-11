"""가드레일 stub — 입력(PII·범위) / 출력(유출).

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 주민등록번호 / 계좌·카드번호 비슷한 패턴
_PII_PATTERNS = [
    re.compile(r"\d{6}[- ]?\d{7}"),          # 주민등록번호
    re.compile(r"\d{3,4}[- ]\d{2,6}[- ]\d{3,6}"),  # 계좌/카드
]

# 연금 범위 키워드(범위 판정 휴리스틱)
_SCOPE_KEYWORDS = ["연금", "IRP", "퇴직", "수령", "공제", "납입", "과세", "소득", "해지", "저축"]

# 이메일은 차단이 아니라 마스킹한다(ADR 0001). 조치가 다르므로 _PII_PATTERNS에 흡수하지 않고 분리 유지.
# ⚠️ 정규식 휴리스틱 stub — TLD 유무로만 이메일을 가른다.
_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


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


def _mask_one(match: re.Match[str]) -> str:
    local, domain = match.group(0).split("@", 1)
    tld = domain.rsplit(".", 1)[1]
    return f"{local[0]}***@{domain[0]}***.{tld}"


def mask_emails(text: str) -> str:
    """이메일을 부분 마스킹한다 — `hong@example.com` → `h***@e***.com`.

    로컬파트와 도메인은 첫 글자만 남기고, 도메인 뒤에는 TLD만 붙인다
    (`hong@mail.co.kr` → `h***@m***.kr` — 중간 레이블 `co`는 버린다).
    TLD가 없는 `@`(`7@8`, `@연금팀`)는 이메일로 보지 않는다.

    fail-closed 방향이라 `report@v2.tar.gz` 같은 조합을 과하게 마스킹할 수 있다(SPEC.md 알려진 한계).
    """
    return _EMAIL_PATTERN.sub(_mask_one, text)


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
