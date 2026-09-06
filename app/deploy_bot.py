"""배포현황 봇 (23강 · Ch3 파이널).

외부 배포/CI 이벤트를 받아 '사람이 볼 한 줄'로 요약해 게시한다. Ch3 다섯 원칙을 하나로:
  · 인젝션 방어 — 요약은 '구조화 필드'에서만. 자유 텍스트(commit_message)는 표시용 데이터일 뿐,
    봇의 행동을 지시하지 못한다(17·18 신뢰 경계). 어떤 외부 텍스트도 행동을 바꾸지 않고, 행동은 코드가 정한다.
  · 신뢰성 5요소(20강, app/mcp_client) — 타임아웃·분류 재시도·상한·폴백·로그.
  · 멱등 — 같은 run_id는 한 번만 게시.
  · 폴백 = fail-closed — 최종 실패 시 '성공'을 지어내지 않고 '확인 불가'로.
게시 자체(reply/webhook)는 주입한다(post_fn) — transport 무관, 테스트 가능.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from app import mcp_client

log = logging.getLogger("pension_qa.deploybot")

# 요약에 쓰는 '구조화 필드'만 화이트리스트. commit_message 등 자유 텍스트는 절대 안 쓴다.
SUMMARY_FIELDS = ("service", "version", "env", "status", "duration", "commits")
# 혹시라도 필드 값에 섞여 들어올 시크릿/PII 흔적을 게시 전 마지막으로 지운다(이중 방어).
_SECRET = re.compile(r"xoxb-[A-Za-z0-9-]+|\bSLACK_BOT_TOKEN\b|\d{6}-\d{7}")
_STATUS_MARK = {"success": "✅ 성공", "failed": "❌ 실패"}


def summarize(event: dict, *, error_rate: str | None = None) -> str:
    """구조화 필드에서만 한 줄 요약을 만든다(인젝션 방어의 핵심)."""
    status = _STATUS_MARK.get(event.get("status", ""), event.get("status", "?"))
    parts = [
        f"{event.get('service','?')}",
        f"{event.get('version','?')} → {event.get('env','?')}",
        status,
        f"{event.get('duration','?')}",
        f"커밋 {event.get('commits','?')}개",
    ]
    if error_rate is not None:  # 모니터링 pull이 얹는 검증 칸
        parts.append(f"배포 후 에러율 {error_rate}")
    line = "  ·  ".join(parts)
    return _SECRET.sub("[제거됨]", line)  # 이중 방어 — 필드에 섞여도 게시엔 안 나감


def post_status(
    post_fn,
    event,
    *,
    out_dir="out",
    monitor=None,
    seen=None,
    timeout=3.0,
    max_retries=3,
):
    """이벤트를 요약해 게시한다. 멱등·신뢰성·폴백·출력(채점 입력)까지.

    monitor: 선택. `monitor(service) -> "0.2% 정상"` 형태의 모니터링 pull(에러율).
    seen: 멱등 집합(run_id). 같은 배포가 두 번 와도 한 번만 게시.
    """
    seen = seen if seen is not None else set()
    run_id = event.get("run_id", "unknown")
    if run_id in seen:
        log.info("deploy dup run_id=%s skip", run_id)  # 멱등
        return None

    error_rate = None
    if monitor is not None:
        # 배포 push 수신 후 배포 직후 에러율을 pull로 검증(실패해도 요약은 나간다 — 폴백)
        rate = mcp_client.call_mcp(
            lambda tool, args, *, timeout: monitor(args["service"]),
            "error_rate",
            {"service": event.get("service")},
            timeout=timeout,
            max_retries=max_retries,
        )
        error_rate = rate if isinstance(rate, str) else None

    summary = summarize(event, error_rate=error_rate)

    # 게시에 신뢰성 5요소 — 최종 실패면 fallback(성공을 지어내지 않는다, fail-closed)
    result = mcp_client.call_mcp(
        lambda tool, args, *, timeout: post_fn(args["summary"]),
        "post_status",
        {"summary": summary},
        timeout=timeout,
        max_retries=max_retries,
    )
    if isinstance(result, mcp_client.Unavailable):
        log.error(
            "deploy post failed run_id=%s -> 확인 불가(성공 지어내지 않음)", run_id
        )
        return result

    seen.add(run_id)
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    (out / f"post_{run_id}.txt").write_text(
        summary, encoding="utf-8"
    )  # 채점 입력(§5 ①②)
    log.info("deploy posted run_id=%s", run_id)  # 관측
    return summary
