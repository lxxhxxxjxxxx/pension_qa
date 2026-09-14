#!/usr/bin/env python3
"""27강 — 부채 지표 수집. 감이 아니라 숫자로, 모듈별로(09강).

"기술 부채"는 추상적이지만 대부분 지표로 뽑힌다. 같은 코드에 같은 스캔을 돌리면 같은 숫자가 나온다
= 부채 측정도 결정적이다(차별점①). 사람이 "좀 지저분한데"라고 하면 사람마다·어제와 오늘이 다르다.

세 지표를 모듈별로 뜬다:
  TODO/FIXME  — 코드에 박힌 '나중에'의 총량. 개발자 본인의 자백이라 제일 정직하다.
  커버리지    — 테스트가 안 닿는 곳 = 부채가 숨는 곳(pytest --cov, pytest-cov 필요)
  mutation    — 테스트가 '밟기만' 하나 '진짜 잡나'(15강). 무거우니 --mutation 을 줄 때만 돈다.

전체 합 하나만 보면 어디를 고칠지 모른다. 모듈별로 떠서 국소화하는 것이 부채 지도다.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"

# 지표가 나쁜 쪽부터 갚는다. 판정 문구는 규칙으로 고정한다(사람이 매번 고민하지 않게).
COVERAGE_BLACKBOX = 50  # 이 밑이면 '테스트가 안 닿는다'
COVERAGE_OK = 90


def todo_counts() -> dict[str, int]:
    """grep -REc 'TODO|FIXME' app/ 과 같은 것을 파이썬으로."""
    out: dict[str, int] = {}
    for p in sorted(APP.glob("*.py")):
        text = p.read_text(encoding="utf-8")
        out[p.name] = len(re.findall(r"TODO|FIXME", text))
    return out


def coverage_percent() -> dict[str, int] | None:
    """pytest --cov=app --cov-report=term 의 모듈별 %. pytest-cov 없으면 None."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--cov=app", "--cov-report=term", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if "unrecognized arguments" in proc.stderr or "--cov" in proc.stderr:
        return None
    out: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"^app/(\S+\.py)\s+\d+\s+\d+\s+(\d+)%", line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out or None


def mutation_score(module: str) -> tuple[int, int] | None:
    """mutmut 3.x: setup.cfg 의 source_paths 를 쓰고 이름 패턴으로 고른다.

    ⚠️ mutmut 3.x 에는 --paths-to-mutate 가 없다(2.x 문법). 그리고 mutants/ 안에서 테스트가
    도니까 setup.cfg 의 also_copy 에 tests 가 import 하는 것(scripts·pension_qa_docs)이
    전부 들어 있어야 한다 — 없으면 'failed to collect stats' 로 죽는다.
    """
    stem = module.replace(".py", "")
    # `mutmut` 실행 파일이 PATH 에 없을 수 있다(venv) — 모듈로 부르는 쪽을 먼저 쓴다.
    for cmd in ([sys.executable, "-m", "mutmut"], ["mutmut"]):
        try:
            proc = subprocess.run(
                [*cmd, "run", f"app.{stem}*"], cwd=ROOT, capture_output=True, text=True
            )
        except FileNotFoundError:
            continue
        killed = len(re.findall(r"^🎉", proc.stdout, re.M))
        survived = len(re.findall(r"^🙁", proc.stdout, re.M))
        if killed + survived:
            return killed, killed + survived
        if "failed to collect stats" in proc.stdout:
            # setup.cfg also_copy 에 테스트가 쓰는 것이 빠졌다는 신호다.
            print(f"⚠️ mutmut 이 {module} 통계를 못 모았다 — setup.cfg also_copy 확인", file=sys.stderr)
            return None
    print("⚠️ mutmut 을 찾지 못했다(pip install mutmut) — mutation 열은 비운다", file=sys.stderr)
    return None


def verdict(todo: int, cov: int | None, mut: tuple[int, int] | None) -> str:
    if cov is not None and cov < COVERAGE_BLACKBOX:
        return "커버부터 — 테스트가 안 닿는다"
    if mut is not None and mut[1] and mut[0] / mut[1] < 0.9:
        return "테스트 보강 — 밟기만 하고 안 잡는 자리가 남았다"
    if todo > 0:
        return f"TODO {todo}건 — 적어둔 '나중에'를 갚을 차례"
    return "양호"


def collect(mutation_for: list[str] | None = None) -> list[dict]:
    todos = todo_counts()
    covs = coverage_percent() or {}
    rows = []
    for name in sorted(todos):
        if name == "__init__.py":
            continue
        mut = mutation_score(name) if mutation_for and name in mutation_for else None
        rows.append(
            {
                "module": name,
                "todo": todos[name],
                "coverage": covs.get(name),
                "mutation": mut,
                "verdict": verdict(todos[name], covs.get(name), mut),
            }
        )
    # 나쁜 순서대로 — 커버리지 낮은 것부터, 같으면 TODO 많은 것부터. 표가 상환 순서를 정한다.
    rows.sort(key=lambda r: (r["coverage"] if r["coverage"] is not None else 999, -r["todo"]))
    return rows


def render(rows: list[dict]) -> str:
    head = f"{'모듈':<20}{'TODO':>5}{'커버':>7}{'mutation':>11}  판정"
    lines = [head, "-" * len(head) * 2]
    for r in rows:
        cov = "—" if r["coverage"] is None else f"{r['coverage']}%"
        mut = "—" if not r["mutation"] else f"{r['mutation'][0]}/{r['mutation'][1]}"
        lines.append(f"{r['module']:<20}{r['todo']:>5}{cov:>7}{mut:>11}  {r['verdict']}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="부채 지표 수집 — 모듈별 부채 지도")
    ap.add_argument("--mutation", nargs="*", metavar="MODULE",
                    help="mutation 까지 (느리다). 예: --mutation guardrails.py")
    ap.add_argument("--json", action="store_true", help="JSON 으로")
    ap.add_argument("--to-backlog", action="store_true",
                    help="나쁜 지표를 BACKLOG.md 에 📊 항목으로 흘려보낸다")
    args = ap.parse_args()

    rows = collect(args.mutation)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(render(rows))

    if args.to_backlog:
        from append_backlog import metrics_to_items, merge_into_backlog  # noqa: E402

        added = merge_into_backlog(metrics_to_items(rows))
        print(f"\nBACKLOG.md 로 흘려보낸 지표 항목: {added}건")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
