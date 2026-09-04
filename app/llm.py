"""LLM 클라이언트 — ANTHROPIC_API_KEY 있으면 호출, 없으면 stub.

20강: 외부 호출 신뢰성 5요소를 LLM 호출에 입혔다.
  ① 타임아웃 명시(LLM_TIMEOUT_S)  ② 재시도는 분류해서 상한 안에서(LLM_MAX_RETRIES, 429·5xx·타임아웃만)
  ③ 조회라 멱등(재시도 안전)  ④ 폴백은 유지("[LLM 오류 fallback]")  ⑤ 모든 갈림길에 로그
재시도 상한 = 비용 캡 (재시도 1회 = 요금 1회). 정책은 docs/adr/0005-external-call-reliability.md.
"""

from __future__ import annotations

import logging
import os
import random
import time

log = logging.getLogger("pension_qa.llm")

SYSTEM = (
    "당신은 연금 안내 도우미입니다. 제공된 근거 문서 범위 안에서만 답하고, "
    "모르면 모른다고 답하세요. 세율·한도는 가상 예시임을 전제합니다."
)

# ② 재시도할 실패만 — 401/403/404 등 상태 불변 오류는 재시도하지 않는다(비용만 태움)
RETRYABLE = {429, 500, 502, 503, 504}
TIMEOUT_S = float(os.environ.get("LLM_TIMEOUT_S", "30"))  # ① 호출 하나의 응답 상한
MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "3"))  # ② 상한 = 비용 캡
FALLBACK_PREFIX = "[LLM 오류 fallback]"

_sleep = time.sleep  # 테스트에서 바꿔 끼운다


def _make_client():
    import anthropic  # 지연 import — 키 없을 땐 패키지도 필요 없다

    return anthropic.Anthropic()


def _classify(e: Exception) -> str:
    """'retry' | 'stop'. 상태 코드가 있으면 RETRYABLE 여부, 없으면 타임아웃·연결 오류만 재시도."""
    status = getattr(e, "status_code", None)
    if status is not None:
        return "retry" if status in RETRYABLE else "stop"
    name = type(e).__name__
    if "Timeout" in name or "Connection" in name:
        return "retry"
    return "stop"


def _retry_after(e: Exception) -> float | None:
    """429 등에 Retry-After 헤더가 있으면 그 초를 존중한다."""
    headers = getattr(getattr(e, "response", None), "headers", None) or {}
    value = headers.get("retry-after") if hasattr(headers, "get") else None
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def answer(
    question: str, contexts: list[str], model: str = "claude-haiku-4-5-20251001"
) -> str:
    prompt = (
        "다음 근거 문서를 참고해 질문에 답하세요.\n\n"
        + "\n\n".join(f"[근거] {c}" for c in contexts)
        + f"\n\n[질문] {question}"
    )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return f"[LLM stub] 근거 {len(contexts)}건 기반 답변 예정 — '{question}'"

    client = _make_client()
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=512,
                system=SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT_S,  # ① 기본값에 기대지 않는다
            )
            log.info("llm ok attempt=%d", attempt)  # ⑤
            return msg.content[0].text
        except Exception as e:  # noqa: BLE001 — 분류는 _classify가 한다
            last_error = e
            kind = _classify(e)
            status = getattr(e, "status_code", None)
            if kind == "stop":
                log.error("llm non-retryable status=%s err=%s", status, e)  # ⑤
                break
            if attempt >= MAX_RETRIES:
                log.error(
                    "llm retries exhausted max=%d status=%s", MAX_RETRIES, status
                )  # ⑤
                break
            wait = _retry_after(e)
            if wait is None:
                wait = (2**attempt) + random.uniform(0, 0.3)  # 지수 백오프 + 지터
            log.warning(
                "llm retry status=%s attempt=%d wait=%.1fs", status, attempt, wait
            )  # ⑤
            _sleep(wait)
    # ④ 폴백 — 조용히 틀린 답 대신 명시적 실패(fail-closed). 로그는 위에서 남겼다.
    return f"{FALLBACK_PREFIX} {last_error}"
