#!/usr/bin/env python3
"""29강 — Claude Code 텔레메트리(OpenTelemetry console exporter) 출력 파서.

collector 없이도 숫자를 뽑기 위한 최소 도구다. `OTEL_LOGS_EXPORTER=console`·`OTEL_METRICS_EXPORTER=console`
로 켜면 Claude Code 가 이벤트·메트릭을 표준출력에 JS 객체 형태로 찍는다(JSON 이 아니라 그대로 읽어야 한다).
  이벤트  body: "claude_code.skill_activated" … attributes: { "skill.name": "code-review", … }
  메트릭  descriptor: { name: "claude_code.cost.usage" … } dataPoints: [ { attributes: {…}, value: 0.0012 } ]

⚠️ 공식 문서(monitoring-usage, 2026-09-15)의 이벤트 표엔 user_prompt·assistant_response·tool_result·api_request·
api_error 5종만 있다. skill_activated·hook_registered·mcp_server_connection·tool_decision 은 표에 없지만
2.1.272 에서 실제로 찍힌다(scripts/mock_otel_console.log 가 그 원본). 문서가 아니라 출력을 믿는다.
"""

from __future__ import annotations

import re
from pathlib import Path

EVENT_RE = re.compile(r'^\s*body:\s*"claude_code\.([\w.]+)",?\s*$')
METRIC_RE = re.compile(r'^\s*name:\s*"claude_code\.([\w.]+)",?\s*$')
ATTR_RE = re.compile(r'^\s*"?([\w.]+)"?:\s*(.+?),?\s*$')
VALUE_RE = re.compile(r"^\s*value:\s*([-\d.eE+]+),?\s*$")


def _val(raw: str) -> str:
    raw = raw.strip().rstrip(",").strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def _read_attrs(lines: list[str], j: int) -> tuple[dict[str, str], int]:
    """lines[j] 가 `attributes: {` 인 자리에서 닫는 `}` 까지 읽는다. 반환: (attrs, 닫는 줄 인덱스)."""
    attrs: dict[str, str] = {}
    if "{}" in lines[j]:
        return attrs, j
    j += 1
    while j < len(lines) and not lines[j].strip().startswith("}"):
        a = ATTR_RE.match(lines[j])
        if a:
            attrs[a.group(1)] = _val(a.group(2))
        j += 1
    return attrs, j


def parse(text: str) -> dict:
    """console 출력 전체 → {"events": [{name, attrs}], "metrics": [{name, attrs, value}]}"""
    events: list[dict] = []
    metrics: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = EVENT_RE.match(lines[i])
        if m:
            name = m.group(1)
            j = i + 1
            while j < len(lines) and "attributes: {" not in lines[j]:
                j += 1
            attrs, j = _read_attrs(lines, j) if j < len(lines) else ({}, j)
            events.append({"name": name, "attrs": attrs})
            i = j + 1
            continue
        m = METRIC_RE.match(lines[i])
        if m:
            name = m.group(1)
            j = i + 1
            cur: dict[str, str] | None = None
            # 다음 레코드(최상위 `{` 또는 다음 descriptor)에서 멈춘다 — 이벤트와 메트릭이 섞여 찍힌다
            while j < len(lines) and lines[j] != "{" and not lines[j].strip().startswith("descriptor:"):
                if "attributes: {" in lines[j]:
                    cur, j = _read_attrs(lines, j)
                else:
                    v = VALUE_RE.match(lines[j])
                    if v and cur is not None:
                        metrics.append({"name": name, "attrs": cur, "value": float(v.group(1))})
                        cur = None
                j += 1
            i = j
            continue
        i += 1
    return {"events": events, "metrics": metrics}


def load(path: str | Path) -> dict:
    return parse(Path(path).read_text(encoding="utf-8", errors="replace"))


def count_events(data: dict, name: str, key: str | None = None) -> dict[str, int]:
    """이벤트 name 을 key 속성값별로 센다. key=None 이면 {"*": 총수}."""
    out: dict[str, int] = {}
    for e in data["events"]:
        if e["name"] != name:
            continue
        k = e["attrs"].get(key, "(없음)") if key else "*"
        out[k] = out.get(k, 0) + 1
    return out


def sum_metric(data: dict, name: str, key: str | None = None) -> dict[str, float]:
    """메트릭 name 의 value 를 key 속성값별로 합한다."""
    out: dict[str, float] = {}
    for m in data["metrics"]:
        if m["name"] != name:
            continue
        k = m["attrs"].get(key, "(없음)") if key else "*"
        out[k] = out.get(k, 0.0) + m["value"]
    return out


if __name__ == "__main__":  # 빠른 확인: python3 scripts/otel_log.py <console.log>
    import sys

    d = load(sys.argv[1])
    names: dict[str, int] = {}
    for e in d["events"]:
        names[e["name"]] = names.get(e["name"], 0) + 1
    for n, c in sorted(names.items(), key=lambda x: -x[1]):
        print(f"{c:4d}  {n}")
    print("skill_activated:", count_events(d, "skill_activated", "skill.name"))
    print("cost.usage by skill:", sum_metric(d, "cost.usage", "skill.name"))
