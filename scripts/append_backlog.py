#!/usr/bin/env python3
"""27강 — 리뷰 산출·스캔 지표를 부채 큐로 라우팅하고 BACKLOG.md 에 결정적으로 append.

26강 `aggregate_reviews.py` 는 **게이트 판정**을 한다 — confirm 된 🔴 Important 가 있으면 머지 차단.
거기서 '폐기'로 찍히는 것에는 두 종류가 섞여 있다.

  - 적대적 검증에서 **논파**된 것(FP): 진짜 폐기다. 백로그에도 안 간다.
  - 표가 모자라 confirm 안 된 **🟡 Nit·🟣 Pre-existing**: '지금 막을 일이 아니다'일 뿐, 부채다.

27강은 그 두 번째 갈래를 백로그로 잇는다. 잡기만 하고 흘려보낼 데가 없으면 루프가 아니라 구멍이다(24강).

큐 라우팅 (결정적 — 심각도와 검증 결과가 큐를 정한다. 사람이 매번 고민하지 않는다):

    논파(FP)                        →  폐기
    confirm + 🔴 Important          →  긴급 큐 · 머지 차단 게이트(14강) — 백로그로 오지 않는다
    그 외 🟡 Nit·🟣 Pre-existing    →  부채 큐 · BACKLOG.md

부채 큐 안에서 다시 **"누가 갚나"** 를 가른다(25강 checklist 수정 라우팅 → 30강 파이널 채점 기준):

    저위험 ∧ 가역 ∧ 테스트 격리  전부 충족  →  자동 큐(에이전트가 상환)
    하나라도 미충족                         →  사람 큐

세 조건 다 **기계가 답한다** — 그래서 이 분기도 사람 기분이 아니라 규칙이다.
append 는 file:line 을 키로 병합한다: 같은 리뷰를 열 번 돌려도 백로그는 한 줄로 수렴한다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "BACKLOG.md"
SEP = " · "

# ── 3조건 판정에 쓰는 규칙표 ────────────────────────────────────────────────
# 규칙은 화면에 보이는 곳에 둔다. 숨겨두면 "왜 자동 큐로 갔는지"를 설명할 수 없다.
LOW_RISK_WORDS = ("매직넘버", "상수", "주석", "docstring", "로깅", "네이밍", "변수명", "포맷", "타이포")
STRUCTURAL_WORDS = ("캐시", "리팩터", "교체", "재작성", "마이그레이션", "스키마", "동시", "레이스", "경로 변경")
# 틀리면 사고가 되는 모듈 — 여기 변경은 아무리 사소해 보여도 자동 상환 대상이 아니다.
CRITICAL_MODULES = ("guardrails.py", "llm.py", "pension_calc.py", "mcp_client.py")


def three_conditions(file: str, note: str) -> dict[str, bool]:
    """저위험 · 가역 · 테스트 격리를 각각 기계로 판정한다."""
    stem = Path(file).stem
    low_risk = any(w in note for w in LOW_RISK_WORDS) and not any(
        m in file for m in CRITICAL_MODULES
    )
    reversible = not any(w in note for w in STRUCTURAL_WORDS)
    test_isolated = (ROOT / "tests" / f"test_{stem}.py").exists()
    return {"저위험": low_risk, "가역": reversible, "테스트격리": test_isolated}


def _why(conds: dict[str, bool]) -> str:
    return " ".join(f"{k}{'✓' if v else '✗'}" for k, v in conds.items())


def route(rows: list[dict]) -> list[dict]:
    """26강 집계 rows(aggregate 결과) → 부채 큐 항목. 긴급·FP는 여기서 걸러진다."""
    items = []
    for r in rows:
        if r["verdict"] == "refuted":
            continue  # 논파된 FP — 진짜 폐기
        if r["decision"] == "confirm" and r["severity"] == "Important":
            continue  # 긴급 큐(게이트) — 백로그 아님
        severity = "Nit" if r["severity"] != "Pre-existing" else "Pre-existing"
        note = r.get("note") or (r.get("notes") or [""])[0]
        conds = three_conditions(r["file"], note)
        items.append(
            {
                "kind": "review",
                "severity": severity,
                "file": r["file"],
                "line": r["line"],
                "note": note,
                "queue": "자동" if all(conds.values()) else "사람",
                "why": _why(conds),
            }
        )
    return items


def metrics_to_items(rows: list[dict]) -> list[dict]:
    """scan_debt 결과 중 **나쁜 것만** 지표 항목으로. 양호한 모듈까지 쌓으면 백로그가 노이즈다."""
    items = []
    for r in rows:
        if r["verdict"] == "양호":
            continue
        cov = "—" if r["coverage"] is None else f"커버 {r['coverage']}%"
        mut = "" if not r["mutation"] else f" · mutation {r['mutation'][0]}/{r['mutation'][1]}"
        items.append(
            {
                "kind": "metric",
                "severity": "지표",
                "file": f"app/{r['module']}",
                "line": 0,
                "note": f"{cov}{mut} · TODO {r['todo']}",
                "queue": "사람",  # 지표성 부채는 범위 산정이 필요하다 — 자동 상환 대상 아님
                "why": r["verdict"],
            }
        )
    return items


# ── BACKLOG.md 읽고/쓰기 — file:line 키 병합으로 수렴시킨다 ──────────────────
ICON = {"Nit": "🟡", "Pre-existing": "🟣", "지표": "📊"}
LINE_RE = re.compile(
    r"^- \[(?P<done>[ xX])\] (?P<icon>🟡|🟣|📊) (?P<sev>\S+)"
    + re.escape(SEP)
    + r"(?P<file>[^ ]+?)(?::(?P<line>\d+))?"
    + re.escape(SEP)
    + r"(?P<note>.*?)"
    + re.escape(SEP)
    + r"(?P<why>.*)$"
)


def _key(item: dict) -> str:
    return f"{item['file']}:{item['line']}"


def read_backlog() -> dict[str, dict]:
    if not BACKLOG.exists():
        return {}
    out: dict[str, dict] = {}
    queue = "사람"
    for line in BACKLOG.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 자동 큐"):
            queue = "자동"
        elif line.startswith("## 사람 큐") or line.startswith("## 지표"):
            queue = "사람"
        m = LINE_RE.match(line)
        if not m:
            continue
        item = {
            "kind": "metric" if m["sev"] == "지표" else "review",
            "severity": m["sev"],
            "file": m["file"],
            "line": int(m["line"] or 0),
            "note": m["note"],
            "queue": queue,
            "why": m["why"],
            "done": m["done"].lower() == "x",
        }
        out[_key(item)] = item
    return out


def render(items: dict[str, dict]) -> str:
    def block(title: str, sel) -> list[str]:
        rows = sorted(
            (i for i in items.values() if sel(i)), key=lambda i: (i["file"], i["line"])
        )
        out = [f"## {title}", ""]
        if not rows:
            out += ["- (없음)", ""]
            return out
        for i in rows:
            box = "x" if i.get("done") else " "
            loc = i["file"] if i["kind"] == "metric" else f"{i['file']}:{i['line']}"
            out.append(
                f"- [{box}] {ICON[i['severity']]} {i['severity']}{SEP}{loc}{SEP}{i['note']}{SEP}{i['why']}"
            )
        out.append("")
        return out

    head = [
        "# 부채 백로그 (자동 축적)",
        "",
        "> `scripts/append_backlog.py` 가 관리한다. **file:line 을 키로 병합**하므로 같은 리뷰를",
        "> 열 번 돌려도 한 줄로 수렴한다(중복이 쌓이면 백로그가 아니라 노이즈다).",
        "> 🔴 Important 는 여기 오지 않는다 — 긴급 큐(머지 차단 게이트, 14강)로 간다.",
        "> 3조건(저위험·가역·테스트 격리)이 전부 ✓면 자동 큐, 하나라도 ✗면 사람 큐(→ 30강 채점 기준).",
        "",
    ]
    body = []
    body += block("자동 큐 — 3조건 전부 충족 (에이전트가 상환)", lambda i: i["queue"] == "자동")
    body += block(
        "사람 큐 — 3조건 중 미충족 있음", lambda i: i["queue"] == "사람" and i["kind"] == "review"
    )
    body += block("지표 — scan_debt 가 흘려보낸 것", lambda i: i["kind"] == "metric")
    return "\n".join(head + body).rstrip() + "\n"


def merge_into_backlog(new_items: list[dict]) -> int:
    """append 는 결정적이다 — 같은 file:line 은 갱신, 없으면 추가. 체크 상태는 보존한다."""
    existing = read_backlog()
    added = 0
    for item in new_items:
        k = _key(item)
        if k in existing:
            item = {**item, "done": existing[k].get("done", False)}
        else:
            added += 1
        existing[k] = item
    BACKLOG.write_text(render(existing), encoding="utf-8")
    return added


# ── Stop / SubagentStop 훅 입력에서 리뷰 산출을 뽑는다 ───────────────────────
# 공식 hooks 문서: 이번 턴의 마지막 어시스턴트 텍스트는 transcript 를 뒤지지 말고
# 입력 JSON 의 last_assistant_message 를 쓴다. SubagentStop 이면 agent_type 도 온다.
REVIEW_LINE_RE = re.compile(
    r"^\s*-\s*\[?(?P<file>[\w./-]+\.py):(?P<line>\d+)\]?\s*(?P<note>.+)$"
)
SECTION_RE = re.compile(r"^#{1,4}\s*(🔴|🟡|🟣)\s*(?P<name>\S+)")


def parse_review_text(text: str) -> list[dict]:
    """25·26강 output-style 고정 포맷(🔴/🟡/🟣 · file:line)이라 파싱이 된다.

    자유 문장이었으면 자동 append 가 불가능하다 — 그 제약이 여기서 자산이 된다.
    """
    items, section = [], None
    for line in text.splitlines():
        m = SECTION_RE.match(line)
        if m:
            section = {"Important": "Important", "Nit": "Nit", "Pre-existing": "Pre-existing"}.get(
                m["name"], m["name"]
            )
            continue
        if section in (None, "Important"):
            continue
        r = REVIEW_LINE_RE.match(line)
        if r:
            note = r["note"].strip(" —-")
            conds = three_conditions(r["file"], note)
            items.append(
                {
                    "kind": "review",
                    "severity": "Pre-existing" if section.startswith("Pre") else "Nit",
                    "file": r["file"],
                    "line": int(r["line"]),
                    "note": note,
                    "queue": "자동" if all(conds.values()) else "사람",
                    "why": _why(conds),
                }
            )
    return items


def from_stdin() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    text = payload.get("last_assistant_message") or ""
    items = parse_review_text(text)
    if not items:
        return 0  # 리뷰 산출이 아닌 턴 — 조용히 통과
    return merge_into_backlog(items)


def main() -> int:
    ap = argparse.ArgumentParser(description="리뷰 산출·지표를 부채 큐로 라우팅해 BACKLOG.md 에 append")
    ap.add_argument("--from-stdin", action="store_true", help="Stop/SubagentStop 훅 입력(JSON)에서")
    ap.add_argument("--from-aggregate", action="store_true",
                    help="26강 집계 결과(고정 픽스처)에서 — 게이트 비대상 갈래를 백로그로")
    args = ap.parse_args()

    if args.from_stdin:
        n = from_stdin()
        print(f"백로그 추가 {n}건")
        return 0

    if args.from_aggregate:
        sys.path.insert(0, str(Path(__file__).parent))
        from aggregate_reviews import _load, _cluster, aggregate  # noqa: E402

        findings = _load(Path(__file__).parent / "mock_reviews.jsonl")
        verdicts = _load(Path(__file__).parent / "mock_verdicts.jsonl")
        rows, _ = aggregate(findings, verdicts)
        # 집계 rows 에는 note 가 없다 — 클러스터에서 첫 note 를 끌어온다.
        notes = {f"{g['file']}:{g['line']}": g["notes"][0] for g in _cluster(findings)}
        for r in rows:
            r["note"] = notes.get(f"{r['file']}:{r['line']}", "")
        items = route(rows)
        n = merge_into_backlog(items)
        print(render(read_backlog()))
        print(f"\n부채 큐로 라우팅 {len(items)}건 (신규 {n}건) — 긴급·FP 는 오지 않았다")
        return 0

    print(render(read_backlog()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
