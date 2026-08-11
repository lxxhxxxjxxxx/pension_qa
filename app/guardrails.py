"""가드레일 stub — 입력(PII·범위) / 출력(유출) / 이메일 마스킹.

⚠️ 의도적으로 허술함(정규식·키워드 휴리스틱). Ch2에서 결정적 게이트로 강화한다.

정책:
- 주민등록번호·계좌/카드번호로 보이는 값 → **차단**(복구 불가능한 식별자)
- 이메일 → **마스킹**(질문 의도는 보존하고 식별자만 가림)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 주민등록번호 / 계좌·카드번호 비슷한 패턴
_PII_PATTERNS = [
    re.compile(r"\d{6}[- ]?\d{7}"),          # 주민등록번호
    re.compile(r"\d{3,4}[- ]\d{2,6}[- ]\d{3,6}"),  # 계좌/카드
]

# 이메일 — 마스킹 대상
_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# 마스킹 시 로컬파트에 남길 앞글자 수(도메인은 그대로 둔다)
_EMAIL_KEEP = 1
_EMAIL_MASK = "***"

# 연금 범위 키워드(범위 판정 휴리스틱)
_SCOPE_KEYWORDS = ["연금", "IRP", "퇴직", "수령", "공제", "납입", "과세", "소득", "해지", "저축"]


@dataclass(frozen=True)
class Check:
    ok: bool
    reason: str = ""


@dataclass(frozen=True)
class Sanitized:
    """마스킹을 거친 텍스트와 무엇을 가렸는지에 대한 기록."""

    text: str
    emails_masked: int = 0

    @property
    def changed(self) -> bool:
        return self.emails_masked > 0


def _mask_email(match: re.Match[str]) -> str:
    local, _, domain = match.group(0).partition("@")
    # 마스크 길이는 고정한다 — 원본 길이가 새어나가지 않도록.
    return f"{local[:_EMAIL_KEEP]}{_EMAIL_MASK}@{domain}"


def mask_emails(text: str) -> tuple[str, int]:
    """이메일을 `h***@example.com` 형태로 가리고 (마스킹된 텍스트, 건수)를 반환."""
    return _EMAIL_PATTERN.subn(_mask_email, text)


def sanitize(text: str) -> Sanitized:
    """입력·출력 공통 정제 — 현재는 이메일 마스킹."""
    masked, count = mask_emails(text)
    return Sanitized(masked, emails_masked=count)


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


# agent 가 순서대로 돌리는 입력 게이트. 게이트 추가는 여기에만 하면 된다.
INPUT_CHECKS = (check_input_pii, check_input_scope)
