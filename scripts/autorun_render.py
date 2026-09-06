#!/usr/bin/env python3
"""21강 — `claude -p --output-format stream-json` 을 사람이 읽는 한 줄씩으로 (장치 ⑥ 관측).
기본 text 출력은 끝날 때까지 아무것도 안 찍혀서 자율 실행이 멈춘 것처럼 보인다. 이 필터가 턴·도구·게이트·결과를 보이게 한다.
종료 줄은 docs/autonomy/작업로그.md 에도 남긴다(장치 ⑤ 흔적)."""

import json
import os
import sys
import time

LOG = os.environ.get("AUTORUN_LOG", "docs/autonomy/작업로그.md")
t0 = time.time()


def line(tag, text):
    print(f"[{time.time() - t0:4.0f}s] {tag:<6} {text}", flush=True)


def first_line(s, n=110):
    s = s.strip().splitlines()
    return (s[0] if s else "")[:n]


for raw in sys.stdin:
    try:
        d = json.loads(raw)
    except ValueError:
        continue
    t = d.get("type")
    msg = d.get("message")
    content = msg.get("content", []) if isinstance(msg, dict) else []
    if isinstance(content, str):  # 문자열 본문(훅 피드백 등)도 한 줄로
        content = [{"type": "text", "text": content}]
    if not isinstance(content, list):
        content = []
    if t == "assistant":
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and b["text"].strip():
                line("claude", first_line(b["text"]))
            elif b.get("type") == "tool_use":
                i = b.get("input") or {}
                arg = i.get("command") or i.get("file_path") or i.get("pattern") or ""
                line("tool", f"{b['name']} {str(arg)[:100]}")
    elif t == "user":
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and b["text"].startswith("Stop hook feedback"):
                line(
                    "gate",
                    "Stop 훅이 멈춤을 막음 → "
                    + b["text"].strip().splitlines()[-1][:100],
                )
            elif b.get("type") == "tool_result" and b.get("is_error"):
                c = b.get("content")
                line(
                    "error",
                    first_line(
                        c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
                    ),
                )
    elif t == "result":
        s = (
            f"{d.get('subtype')} · turns={d.get('num_turns')} · "
            f"cost=${d.get('total_cost_usd', 0):.2f} · {d.get('duration_ms', 0) / 1000:.0f}s"
        )
        line("result", s)
        try:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"- [{time.strftime('%H:%M:%S')}] ■ autorun 종료 {s}\n")
        except OSError:
            pass
