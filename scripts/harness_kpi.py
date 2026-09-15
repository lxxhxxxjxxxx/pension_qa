#!/usr/bin/env python3
"""29강 — 하네스 KPI, 두 단계. "이 하네스가 값을 하나"를 감이 아니라 숫자로.

아래층 프록시(하네스가 일한다는 간접 신호)는 게이밍된다 — 리뷰어가 마구 지적할수록 적발률이 오른다(15·27강 게이밍 계열).
그래서 위층에 결과 지표(MTTD·MTTR·오탐률)를 둔다. 프록시만 좋아지고 결과가 안 움직이면 하네스가 헛도는 것.

  프록시  적발률      confirm 된 🔴 Important / 리뷰(PR) 수      26강 집계(aggregate_reviews)에서 — 고정 포맷이라 셀 수 있다
          작업당 비용  OTel cost.usage 합 / PR 수                  텔레메트리 로그 필요
          usage       token.usage · skill_activated              텔레메트리 로그 필요
  결과    오탐률      refuted / 검증된 발견                        26강 verdicts
          MTTD·MTTR   장애 ADR 의 `발생:`·`발견:`·`복구:` 시각 차   기록이 없으면 "미기록" — 지어내지 않는다

  python3 scripts/harness_kpi.py [--otel-log docs/otel/console.log] [--prs N] [--write x.md]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts import otel_log  # noqa: E402
from scripts.aggregate_reviews import _load, aggregate  # noqa: E402

TS = re.compile(r"^- (발생|발견|복구):\s*(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2})", re.M)


def proxy_metrics(data: dict | None, prs: int) -> list[dict]:
    rows, gate = aggregate(_load(ROOT / "scripts" / "mock_reviews.jsonl"), _load(ROOT / "scripts" / "mock_verdicts.jsonl"))
    out = [{"kpi": "적발률", "value": f"{gate}건 / {prs} PR", "src": "26강 집계 confirm 🔴 Important(고정 포맷이라 셀 수 있다)"}]
    if data is None:
        out.append({"kpi": "작업당 비용", "value": "근거 없음", "src": "텔레메트리 로그 없음(--otel-log)"})
        out.append({"kpi": "usage", "value": "근거 없음", "src": "텔레메트리 로그 없음"})
        return out
    cost = sum(m["value"] for m in data["metrics"] if m["name"] == "cost.usage")
    by_skill = otel_log.sum_metric(data, "cost.usage", "skill.name")
    tok = otel_log.sum_metric(data, "token.usage", "type")
    act = otel_log.count_events(data, "skill_activated", "skill.name")
    cache = tok.get("cacheRead", 0.0) / max(1.0, sum(tok.values()))
    out.append({"kpi": "작업당 비용", "value": f"${cost / max(prs, 1):.3f} / PR", "src": f"cost.usage 합 ${cost:.3f} · 스킬별 " + ", ".join(f"{k} ${v:.3f}" for k, v in by_skill.items())})
    out.append({"kpi": "usage", "value": f"토큰 {int(sum(tok.values())):,} · 캐시 읽기 {cache:.0%}", "src": "token.usage(type) · skill_activated " + ", ".join(f"{k} {v}" for k, v in act.items())})
    return out


def outcome_metrics() -> list[dict]:
    verdicts = _load(ROOT / "scripts" / "mock_verdicts.jsonl")
    judged = [v for v in verdicts if v["verdict"] in ("survived", "refuted")]
    fp = sum(1 for v in judged if v["verdict"] == "refuted")
    out = [{"kpi": "오탐률", "value": f"{fp}/{len(judged)} = {fp / len(judged):.0%}" if judged else "근거 없음", "src": "26강 verdicts refuted / 검증된 발견 — false positive 의 KPI 판"}]
    found = []
    for adr in sorted((ROOT / "docs" / "adr").glob("*.md")):
        text = adr.read_text(encoding="utf-8")
        if "장애" not in text.splitlines()[0]:
            continue
        ts = {k: datetime.fromisoformat(v.replace(" ", "T")) for k, v in TS.findall(text)}
        if {"발생", "발견", "복구"} <= ts.keys():
            found.append((adr.name, (ts["발견"] - ts["발생"]).total_seconds() / 60, (ts["복구"] - ts["발견"]).total_seconds() / 60))
        else:
            found.append((adr.name, None, None))
    if not found:
        out.append({"kpi": "MTTD · MTTR", "value": "근거 없음", "src": "장애 ADR 없음"})
    else:
        ok = [f for f in found if f[1] is not None]
        if ok:
            mttd = sum(f[1] for f in ok) / len(ok)
            mttr = sum(f[2] for f in ok) / len(ok)
            out.append({"kpi": "MTTD · MTTR", "value": f"{mttd:.0f}분 · {mttr:.0f}분", "src": f"장애 ADR {len(ok)}건의 발생→발견→복구 시각"})
        else:
            out.append({"kpi": "MTTD · MTTR", "value": "미기록", "src": f"장애 ADR {len(found)}건({found[0][0]})에 `- 발생:`·`- 발견:`·`- 복구:` 시각이 없다 — 다음 장애부터 기록해야 산출된다"})
    return out


def render(proxy: list[dict], outcome: list[dict]) -> str:
    out = ["| 층 | KPI | 값 | 근거 |", "|---|---|---|---|"]
    out += [f"| 프록시 | {r['kpi']} | {r['value']} | {r['src']} |" for r in proxy]
    out += [f"| 결과 | {r['kpi']} | {r['value']} | {r['src']} |" for r in outcome]
    out.append("")
    out.append("판정 규칙: 프록시만 좋아지고 결과(오탐률·MTTD·MTTR)가 안 움직이면 하네스가 헛도는 것. '미기록'은 0이 아니다 — 기록 형식부터.")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--otel-log")
    ap.add_argument("--prs", type=int, default=1, help="기간 내 리뷰한 PR 수(기본 1 = 26강 가상 PR)")
    ap.add_argument("--write")
    a = ap.parse_args(argv)
    data = otel_log.load(a.otel_log) if a.otel_log else None
    text = render(proxy_metrics(data, a.prs), outcome_metrics())
    print(text)
    if a.write:
        with open(a.write, "a", encoding="utf-8") as f:
            f.write("\n## 2) KPI — 두 단계\n\n" + text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
