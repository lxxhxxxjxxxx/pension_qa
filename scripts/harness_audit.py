#!/usr/bin/env python3
"""29강 — 하네스 자가점검. 여섯 칸을 감이 아니라 근거로 ✅/⚠️/❌/⚪ 판정한다.

27강이 코드 부채를 숫자로 쟀다면(scan_debt) 이건 **하네스 부채**다. 하네스도 코드라 시간이 지나면 코드베이스와
어긋난다 — 규칙이 거짓이 되고, 게이트가 형식이 되고, 스킬은 안 불리고, 훅은 왜 있는지 잊힌다.
같은 레포에 같은 점검을 돌리면 같은 판정이 나온다(차별점①) — 사람마다·그때그때 다른 "느낌"이 아니다.

  대상          질문                            근거
  CLAUDE.md     적힌 경로·명령이 아직 실재하나    파일 실재 대조
  게이트        아직 걸리나 / 항상 경고만 하나    harness_check.sh · 스킬의 결정적 검증(!) 줄을 실제 실행
  스킬          실제로 불리나                    OTel skill_activated · user_prompt.command_name (로그 없으면 ⚪)
  훅            등록·실재·실행권한 / 돈 흔적      settings.json ↔ .claude/hooks · hook_registered · BACKLOG·작업로그
  서브에이전트  정의가 유효하고 호출되나          agents/*.md model · OTel agent.name (로그 없으면 ⚪)
  플러그인      .claude/ 와 같은가 · bump 필요한가  build_plugin --check · version 이후 .claude/ 커밋

  python3 scripts/harness_audit.py                                  # 표
  python3 scripts/harness_audit.py --otel-log docs/otel/console.log # 텔레메트리 근거까지
  python3 scripts/harness_audit.py --write docs/runbook/x.md        # 리포트 파일
판정 규칙은 여기 고정한다. ⚠️/❌ 는 exit 1 — 6개월 루틴(harness_review.sh)이 이걸 게이트로 쓴다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts import otel_log  # noqa: E402
from scripts import build_plugin  # noqa: E402

OK, WARN, DEAD, NA = "✅ 유효", "⚠️ 갱신", "❌ 폐기/수리", "⚪ 근거 없음"
MONEY_MODULES = ("app/pension_calc.py", "app/agent.py")  # CLAUDE.md "금액 계산" 경로


def _run(cmd: str, timeout: int = 120) -> tuple[int, str]:
    p = subprocess.run(["bash", "-c", cmd], cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def _git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


# ── 1. CLAUDE.md ──────────────────────────────────────────────────────────────
def audit_claude_md(root: Path = ROOT) -> dict:
    """CLAUDE.md 가 백틱으로 가리키는 경로가 아직 실재하나 — 거짓말하는 줄은 에이전트를 없는 파일로 보낸다."""
    text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    refs = set(re.findall(r"`((?:app|docs|scripts|tests|data|\.claude|\.claude-plugin|plugins)/[^`\s]+)`", text))
    refs |= set(re.findall(r"@(README\.md)", text))
    refs = {r for r in refs if "*" not in r}  # 글롭은 실재 대조 대상이 아니다
    lies = sorted(r for r in refs if not (root / r.rstrip("/")).exists())
    # 모듈 경계 규칙(가드레일은 guardrails.py 한 곳) — PII 정규식이 다른 모듈에 새지 않았나
    leak = [
        str(p.relative_to(root))
        for p in (root / "app").glob("*.py")
        if p.name != "guardrails.py" and re.search(r"re\.(compile|search|match|findall)\([^)]*\\d\{6\}", p.read_text(encoding="utf-8"))
    ]
    evidence = f"경로 참조 {len(refs)}개 실재 대조"
    if lies:
        return {"target": "CLAUDE.md", "q": "적힌 경로·규칙이 아직 맞나", "verdict": WARN, "evidence": f"{evidence} — 없는 경로: {', '.join(lies)}"}
    if leak:
        return {"target": "CLAUDE.md", "q": "적힌 경로·규칙이 아직 맞나", "verdict": WARN, "evidence": f"{evidence} ✓ · 가드레일 한 곳 규칙 위반 후보: {', '.join(leak)}"}
    return {"target": "CLAUDE.md", "q": "적힌 경로·규칙이 아직 맞나", "verdict": OK, "evidence": f"{evidence}, 전부 실재 · 가드레일 한 곳 규칙 ✓"}


# ── 2. 게이트 ─────────────────────────────────────────────────────────────────
def skill_gate_lines() -> list[str]:
    """13강 code-review 스킬의 결정적 검증 줄(`!`cmd`)을 뽑는다."""
    skill = ROOT / ".claude" / "skills" / "code-review" / "SKILL.md"
    return re.findall(r"^!`([^`]+)`", skill.read_text(encoding="utf-8"), flags=re.M)


def audit_gates() -> dict:
    rc, out = _run("bash harness_check.sh")
    m = re.search(r"PASS (\d)/(\d)", out)
    passed = f"harness_check {m.group(0) if m else out[:40]}"
    problems: list[str] = []
    if not m or m.group(1) != m.group(2):
        problems.append(passed)
    for cmd in skill_gate_lines():
        if "$ARGUMENTS" in cmd or "pytest" in cmd:
            continue  # diff 인자·테스트는 리뷰 시점 것 — 여기선 grep 게이트만
        rc, out = _run(cmd)
        if "OK:" in out:
            continue
        # 경고를 냈다 — 그 경고가 규칙 범위(금액 경로) 안인가, 밖(=오탐, 항상 경고)인가
        hits = [l for l in out.splitlines() if l.strip()]
        targets = re.findall(r"app/[\w/]*\.py", cmd)
        def _file(h: str) -> str:  # 여러 파일 grep 은 'app/x.py:N:' · 단일 파일이면 인자가 곧 파일
            return h.split(":")[0] if h.startswith("app/") else (targets[0] if len(targets) == 1 else "")
        outside = [h for h in hits if _file(h) and not _file(h).startswith(MONEY_MODULES)] if "float" in cmd else []
        if "float" in cmd and hits and outside and len(outside) == len(hits):
            problems.append(f"`{cmd.split('||')[0].strip()}` 가 규칙 밖 모듈에서 항상 경고({len(hits)}줄: {_file(outside[0])} …) — OK 분기 미도달 = 장식")
        elif hits:
            problems.append(f"`{cmd.split('||')[0].strip()}` 경고 {len(hits)}줄 — 리뷰 대상")
    if problems:
        return {"target": "게이트", "q": "아직 걸리나 · 항상 경고만 하지 않나", "verdict": WARN, "evidence": " / ".join(problems)}
    return {"target": "게이트", "q": "아직 걸리나 · 항상 경고만 하지 않나", "verdict": OK, "evidence": f"{passed} · 스킬 grep 게이트 {len(skill_gate_lines())}줄 중 grep {sum(1 for c in skill_gate_lines() if 'grep' in c)}개 전부 OK 분기 도달"}


# ── 3. 스킬 ───────────────────────────────────────────────────────────────────
def audit_skills(data: dict | None) -> dict:
    skills = sorted(p.parent.name for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    commands = sorted(p.stem for p in (ROOT / ".claude" / "commands").glob("*.md"))
    names = skills + commands
    if data is None:
        return {"target": "스킬", "q": "실제로 불리나", "verdict": NA, "evidence": f"정의 {len(names)}개({', '.join(names)}) — 텔레메트리 로그 없음. `scripts/otel_console.py on` 뒤 세션 로그를 --otel-log 로"}
    act = otel_log.count_events(data, "skill_activated", "skill.name")
    cmd = otel_log.count_events(data, "user_prompt", "command_name")
    counts = {**{n: act.get(n, 0) for n in skills}, **{n: cmd.get(n, 0) for n in commands}}
    dead = [n for n, c in counts.items() if c == 0]
    ev = " · ".join(f"{n} {c}회" for n, c in counts.items())
    if dead:
        return {"target": "스킬", "q": "실제로 불리나", "verdict": DEAD if len(dead) == len(names) else WARN, "evidence": f"skill_activated·command_name — {ev} → 0회: {', '.join(dead)}(죽은 무게 후보 — 로그 기간이 충분한가 먼저)"}
    return {"target": "스킬", "q": "실제로 불리나", "verdict": OK, "evidence": f"skill_activated·command_name — {ev}"}


# ── 4. 훅 ─────────────────────────────────────────────────────────────────────
def hook_commands() -> list[tuple[str, str]]:
    cfg = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    out = []
    for event, groups in cfg.get("hooks", {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                out.append((event, h.get("command", "")))
    return out


def audit_hooks(data: dict | None) -> dict:
    cmds = hook_commands()
    scripts_dir = ROOT / ".claude" / "hooks"
    referenced = set()
    broken = []
    for event, cmd in cmds:
        for s in re.findall(r"\.claude/hooks/([\w.-]+\.sh)", cmd):
            referenced.add(s)
            p = scripts_dir / s
            if not p.exists():
                broken.append(f"{event}: {s} 없음")
            elif not os.access(p, os.X_OK):
                broken.append(f"{event}: {s} 실행권한 없음")
    unreferenced = sorted(p.name for p in scripts_dir.glob("*.sh") if p.name not in referenced)
    traces = []
    backlog = ROOT / "BACKLOG.md"
    if backlog.exists():
        n_items = len(re.findall(r"^- \[ \]", backlog.read_text(encoding="utf-8"), flags=re.M))
        traces.append(f"BACKLOG {n_items}건(append-backlog)")
    log = ROOT / "docs" / "autonomy" / "작업로그.md"
    if log.exists():
        traces.append(f"작업로그 게이트 줄 {len(re.findall(r'게이트 차단|게이트 .*미통과|초록', log.read_text(encoding='utf-8')))}(gate-pytest)")
    reg = ""
    if data is not None:
        r = otel_log.count_events(data, "hook_registered", "hook_event")
        reg = f" · hook_registered {sum(r.values())}건({', '.join(f'{k} {v}' for k, v in r.items())}) ↔ settings {len(cmds)}건"
    base = f"settings {len(cmds)}건 ↔ 스크립트 {len(referenced)}개 실재·실행권한"
    if broken:
        return {"target": "훅", "q": "등록·실재·실행되나 · 왜 있는지 남았나", "verdict": DEAD, "evidence": f"{base} — 깨짐: {', '.join(broken)}"}
    if unreferenced:
        return {"target": "훅", "q": "등록·실재·실행되나 · 왜 있는지 남았나", "verdict": WARN, "evidence": f"{base} ✓ · 등록 안 된 스크립트(죽은 훅): {', '.join(unreferenced)}"}
    return {"target": "훅", "q": "등록·실재·실행되나 · 왜 있는지 남았나", "verdict": OK, "evidence": f"{base} ✓ · 흔적: {' · '.join(traces)}{reg}"}


# ── 5. 서브에이전트 ───────────────────────────────────────────────────────────
def audit_agents(data: dict | None) -> dict:
    agents = sorted((ROOT / ".claude" / "agents").glob("*.md"))
    bad = []
    for a in agents:
        fm = a.read_text(encoding="utf-8").split("---")[1] if a.read_text(encoding="utf-8").startswith("---") else ""
        m = re.search(r"^model:\s*(\S+)", fm, flags=re.M)
        if not m or m.group(1) not in {"haiku", "sonnet", "opus", "inherit"}:
            bad.append(f"{a.stem}: model {m.group(1) if m else '없음'}")
    ev = f"정의 {len(agents)}개 · model 필드 {'전부 유효' if not bad else '문제 ' + ', '.join(bad)}"
    if bad:
        return {"target": "서브에이전트", "q": "정의가 유효하고 호출되나", "verdict": WARN, "evidence": ev}
    if data is None:
        return {"target": "서브에이전트", "q": "정의가 유효하고 호출되나", "verdict": NA, "evidence": ev + " — 호출 수는 텔레메트리 로그 필요(cost.usage agent.name)"}
    calls = otel_log.sum_metric(data, "cost.usage", "agent.name")
    calls.pop("(없음)", None)
    if not calls:
        return {"target": "서브에이전트", "q": "정의가 유효하고 호출되나", "verdict": NA, "evidence": ev + " · 로그 기간 내 호출 없음(agent.name 없음) — 리뷰 세션이 든 로그로 다시. 계속 0이면 25·26강 흐름이 끊긴 것"}
    return {"target": "서브에이전트", "q": "정의가 유효하고 호출되나", "verdict": OK, "evidence": ev + " · 호출: " + ", ".join(f"{k} ${v:.3f}" for k, v in calls.items())}


# ── 6. 플러그인 ───────────────────────────────────────────────────────────────
def audit_plugin() -> dict:
    manifest = ROOT / "plugins" / "ai-product-harness" / ".claude-plugin" / "plugin.json"
    version = json.loads(manifest.read_text(encoding="utf-8")).get("version", "(없음)")
    drift = build_plugin.check()
    last_bump = _git("log", "-1", "--format=%h", "-S", f'"version": "{version}"', "--", str(manifest.relative_to(ROOT)))
    after = _git("log", "--format=%h", f"{last_bump}..HEAD", "--", ".claude") if last_bump else ""
    pending = [c for c in after.splitlines() if c]
    ev = f"version {version} · 드리프트 {len(drift)}"
    if drift:
        return {"target": "플러그인", "q": ".claude/ 와 같은가 · bump 필요한가", "verdict": DEAD, "evidence": ev + f" — `build_plugin.py` 재빌드 필요: {drift[0]} …"}
    if pending:
        return {"target": "플러그인", "q": ".claude/ 와 같은가 · bump 필요한가", "verdict": WARN, "evidence": ev + f" · {version} 이후 .claude/ 커밋 {len(pending)}건({', '.join(pending[:3])}) — 팀은 아직 옛 버전. bump → `/plugin update`"}
    return {"target": "플러그인", "q": ".claude/ 와 같은가 · bump 필요한가", "verdict": OK, "evidence": ev + f" · {version} 이후 .claude/ 변경 없음"}


def audit(otel_log_path: str | None = None) -> list[dict]:
    data = otel_log.load(otel_log_path) if otel_log_path else None
    return [audit_claude_md(), audit_gates(), audit_skills(data), audit_hooks(data), audit_agents(data), audit_plugin()]


def render(rows: list[dict]) -> str:
    out = ["| 대상 | 질문 | 판정 | 근거 |", "|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['target']} | {r['q']} | {r['verdict']} | {r['evidence']} |")
    todo = [r for r in rows if r["verdict"] in (WARN, DEAD)]
    na = [r for r in rows if r["verdict"] == NA]
    out.append("")
    out.append(f"결정 필요: {len(todo)}건" + (" — " + ", ".join(r["target"] for r in todo) if todo else "") + (f" · 근거 없음 {len(na)}건(텔레메트리 로그로 채울 것)" if na else ""))
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--otel-log", help="console exporter 출력 파일(scripts/otel_console.py on 뒤 tee 한 것)")
    ap.add_argument("--write", help="리포트를 이 경로에 쓴다(markdown)")
    a = ap.parse_args(argv)
    rows = audit(a.otel_log)
    text = render(rows)
    print(text)
    if a.write:
        Path(a.write).write_text("## 1) 자가점검 — 하네스 6종\n\n" + text + "\n", encoding="utf-8")
    return 1 if any(r["verdict"] in (WARN, DEAD) for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
