#!/usr/bin/env python3
"""26강 — 확률적 리뷰어 N개의 발견을 결정적 규칙으로 집계 (차별점①의 정점).

25강 output-style이 세 리뷰어를 같은 포맷(🔴/🟡/🟣·file:line)으로 뱉게 했기에, file:line으로 정렬·묶어
표를 셀 수 있다. 판정에 사람 주관 0 — 같은 입력이면 같은 판정. 리뷰어를 3→10개로 늘려도 로직 불변(규칙이 스케일).

집계 규칙(결정적):
  1) 같은 file:line(±LINE_TOL 또는 같은 함수)을 ≥2 리뷰어가 독립 지적  → confirm
  2) 1표라도 적대적 검증을 '기계 증거'(grep/test)로 통과            → confirm
  3) 적대적 검증에서 논파(FP), 또는 1표+증거 없음                   → 폐기
  게이트: confirm 된 🔴 Important 수 > 0  →  머지 차단 (25강과 동일)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LINE_TOL = (
    3  # ±몇 줄은 같은 발견으로 묶는다(42/43을 다른 발견으로 세면 2표가 1표 둘로 쪼개짐)
)


def _cluster(findings):
    """(file) 안에서 line을 ±LINE_TOL로 묶어 발견 그룹을 만든다."""
    groups = []  # {file, line, severity, reviewers:set, notes:[]}
    for f in sorted(findings, key=lambda x: (x["file"], x["line"])):
        g = next(
            (
                g
                for g in groups
                if g["file"] == f["file"] and abs(g["line"] - f["line"]) <= LINE_TOL
            ),
            None,
        )
        if g is None:
            g = {
                "file": f["file"],
                "line": f["line"],
                "severity": f["severity"],
                "reviewers": set(),
                "notes": [],
            }
            groups.append(g)
        g["reviewers"].add(f["reviewer"])
        g["notes"].append(f["note"])
        if f["severity"] == "Important":
            g["severity"] = "Important"  # 한 명이라도 Important면 Important로
    return groups


def aggregate(findings, verdicts):
    vmap = {(v["file"], v["line"]): v for v in verdicts}

    def verdict_for(g):
        for (vf, vl), v in vmap.items():
            if vf == g["file"] and abs(vl - g["line"]) <= LINE_TOL:
                return v
        return None

    rows = []
    for g in _cluster(findings):
        votes = len(g["reviewers"])
        v = verdict_for(g)
        refuted = v is not None and v["verdict"] == "refuted"
        has_evidence = (
            v is not None
            and v["verdict"] == "survived"
            and v.get("evidence") in ("grep", "test")
        )
        if refuted:
            decision, rule = "폐기", "규칙3(논파 FP)"
        elif votes >= 2:
            decision, rule = "confirm", "규칙1(≥2표)"
        elif votes >= 1 and has_evidence:
            decision, rule = "confirm", "규칙2(1표+기계증거)"
        else:
            decision, rule = "폐기", "규칙3(1표+증거없음)"
        rows.append(
            {
                "file": g["file"],
                "line": g["line"],
                "severity": g["severity"],
                "votes": votes,
                "reviewers": sorted(g["reviewers"]),
                "verdict": (v["verdict"] if v else "-"),
                "evidence": (v.get("evidence") if v else None),
                "decision": decision,
                "rule": rule,
            }
        )
    confirmed_important = sum(
        1 for r in rows if r["decision"] == "confirm" and r["severity"] == "Important"
    )
    return rows, confirmed_important


def _load(path):
    return [
        json.loads(l)
        for l in Path(path).read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]


def main():
    base = Path(__file__).parent
    findings = _load(base / "mock_reviews.jsonl")
    verdicts = _load(base / "mock_verdicts.jsonl")
    rows, gate = aggregate(findings, verdicts)
    print(f"{'file:line':<24}{'표':>3} {'적대검증':<12}{'판정':<10}규칙")
    for r in rows:
        fl = f"{r['file']}:{r['line']}"
        adv = f"{r['verdict']}{'/'+r['evidence'] if r['evidence'] else ''}"
        print(f"{fl:<24}{r['votes']:>3} {adv:<12}{r['decision']:<10}{r['rule']}")
    print(
        f"\nconfirm된 🔴 Important = {gate}개  →  {'GATE: 머지 차단' if gate > 0 else 'GATE: 통과'}"
    )
    return 0 if gate == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
