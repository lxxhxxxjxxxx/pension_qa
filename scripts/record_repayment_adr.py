#!/usr/bin/env python3
"""30강 — 상환 결정을 ADR 로 자동 기록하고 BACKLOG 항목을 체크한다. "왜 이걸 자동으로 갚았나"가 남아야 24강 ⑤(지식 증발)를 피한다.

  python3 scripts/record_repayment_adr.py app/retriever.py:35 --commit <sha> [--gate "검문 5/5"]

ADR 번호는 docs/adr/ 의 다음 번호. 같은 항목을 두 번 기록하면 기존 ADR 을 그대로 두고 exit 0(멱등 — 23강).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "docs" / "adr"
sys.path.insert(0, str(ROOT / "scripts"))


def next_number(adr_dir: Path = ADR_DIR) -> int:
    nums = [int(m.group(1)) for p in adr_dir.glob("*.md") if (m := re.match(r"(\d{4})-", p.name))]
    return (max(nums) if nums else 0) + 1


def find_backlog_item(item: str, backlog: Path):
    import append_backlog as ab

    ab.BACKLOG = backlog
    items = ab.read_backlog()
    return ab, items, items.get(item)


def record(item: str, commit: str, gate: str, adr_dir: Path = ADR_DIR, backlog: Path = ROOT / "BACKLOG.md", today: str | None = None) -> Path:
    ab, items, entry = find_backlog_item(item, backlog)
    if entry is None:
        raise SystemExit(f"BACKLOG 에 {item} 이 없다 — 백로그 밖의 것을 갚았다면 그건 자동 상환이 아니다")
    if entry["queue"] != "자동":
        raise SystemExit(f"{item} 은 사람 큐다({entry['why']}) — 에이전트가 갚을 항목이 아니다(3조건)")
    stem = Path(entry["file"]).stem
    existing = sorted(adr_dir.glob(f"*-repay-{stem}-{entry['line']}.md"))
    if existing:
        return existing[0]
    n = next_number(adr_dir)
    path = adr_dir / f"{n:04d}-repay-{stem}-{entry['line']}.md"
    today = today or dt.date.today().isoformat()
    text = f"""# ADR {n:04d} — 자동 상환: {item}

- 상태: 채택 (30강 부채 에이전트 · {today})
- 맥락: `BACKLOG.md` 자동 큐 항목 — {entry['severity']} · {entry['note']}
  3조건 판정(27강, 기계): {entry['why']} → 자동 큐. 감시자(debt-scanner)는 표시만 했고, 상환은 별도 에이전트(debt-repayer)가 이 한 항목만 고쳤다.
- 결정: 커밋 `{commit}` 로 상환. 검문(scripts/repay_gate.sh): {gate}. 위 검문을 통과한 것만 머지한다 — 실패·범위 밖은 사람 확인.
- 결과: 백로그에서 이 항목을 체크한다(같은 file:line 은 다시 스캔돼도 [x] 로 보존 — 27강 병합 규칙). 되돌리려면 이 커밋 하나를 revert 하면 된다(가역 ✓).
"""
    path.write_text(text, encoding="utf-8")
    entry["done"] = True
    backlog.write_text(ab.render(items), encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="자동 상환을 ADR 로 기록하고 BACKLOG 항목을 체크")
    ap.add_argument("item", help="file:line — BACKLOG 자동 큐의 키")
    ap.add_argument("--commit", required=True, help="상환 커밋 sha")
    ap.add_argument("--gate", default="검문 5/5", help="repay_gate.sh 결과 한 줄")
    a = ap.parse_args()
    p = record(a.item, a.commit, a.gate)
    print(f"→ {p.relative_to(ROOT)} · BACKLOG.md 체크")
    return 0


if __name__ == "__main__":
    sys.exit(main())
