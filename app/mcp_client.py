"""외부 MCP(또는 임의 외부) 호출에 신뢰성 5요소를 입힌 래퍼 (22강).

20강 `llm.py` 가 LLM 호출에 입힌 것과 같은 원칙을 MCP 도구 호출에 적용한다 —
① 타임아웃 상한 ② 분류 재시도(5xx·타임아웃만, 401/404 제외) ③ 상한=비용 캡
④ 폴백(캐시 stale → 없으면 보수적 실패=fail-closed) ⑤ 모든 갈림길 로그.
호출 자체(`invoke`)는 주입한다 — 이 모듈은 '견디는 방법'만 담는다(transport 무관, 테스트 가능).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

log = logging.getLogger("pension_qa.mcp")

RETRYABLE = {
    500,
    502,
    503,
    504,
}  # 5xx·타임아웃만 재시도. 401/403/404는 재시도 금지(비용만 태움)
WRITE_HINTS = ("write", "create", "update", "delete", "put", "post")


class MCPTimeout(Exception):
    """도구 호출이 타임아웃 상한을 넘었다."""


class MCPHTTPError(Exception):
    def __init__(self, status: int):
        super().__init__(f"status={status}")
        self.status = status


@dataclass
class Unavailable:
    """폴백조차 없을 때의 보수적 실패(fail-closed) — 조용히 틀린 값 대신."""

    reason: str = "확인할 수 없습니다(확인 필요)"


def is_write_tool(tool: str) -> bool:
    """도구 이름이 쓰기성인지 — 읽기 전용 계약 검사(게이트가 강제, 여기선 판정만)."""
    return any(h in tool.lower() for h in WRITE_HINTS)


def _classify(e: Exception) -> str:
    """'retry' | 'stop'."""
    if isinstance(e, MCPTimeout):
        return "retry"
    if isinstance(e, MCPHTTPError):
        return "retry" if e.status in RETRYABLE else "stop"
    return "stop"


def call_mcp(
    invoke, tool, args, *, timeout=3.0, max_retries=3, cache_get=None, _sleep=time.sleep
):
    """`invoke(tool, args, timeout=…)` 를 신뢰성 5요소로 감싼다."""
    last = None
    for attempt in range(max_retries + 1):  # ③ 상한
        try:
            r = invoke(tool, args, timeout=timeout)  # ① 타임아웃
            log.info("mcp ok tool=%s attempt=%d", tool, attempt)  # ⑤
            return r
        except Exception as e:  # noqa: BLE001 — 분류는 _classify 가 한다
            last = e
            if _classify(e) == "stop":
                log.error("mcp non-retryable tool=%s err=%r", tool, e)  # ⑤
                break
            log.warning("mcp retry tool=%s attempt=%d err=%r", tool, attempt, e)  # ⑤
            if attempt < max_retries:
                _sleep(2**attempt)  # ② 지수 백오프
    return _fallback(tool, cache_get, last)  # ④


def _fallback(tool, cache_get, last):
    if cache_get is not None:
        cached = cache_get(tool)
        if cached is not None:
            log.warning("mcp fallback=cache tool=%s stale last=%r", tool, last)  # ⑤
            return cached
    log.error("mcp fallback=none tool=%s -> conservative last=%r", tool, last)  # ⑤
    return Unavailable()
