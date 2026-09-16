#!/usr/bin/env python3
"""30강 — 아키텍처 가드. 아키텍처 규칙을 grep(정규식)으로 **결정적으로** 검사한다. 같은 규칙을 두 층에서 쓴다.

  훅 층   `--hook`      PreToolUse Edit|Write 의 입력 JSON(stdin)에서 *들어올 내용*을 검사한다.
                        위반이면 exit 2 — 편집이 파일에 닿기 전에 막힌다(14강 exit 2 게이트를 아키텍처에).
                        PostToolUse 로 걸면 이미 파일에 닿은 뒤라 못 막는다(공식 문서: 도구는 이미 실행됐다).
  파일 층 `<파일…>`     이미 파일에 있는 것을 검사한다 — CI 사전 머지 게이트·채점(`scripts/grade_final.sh`).
                        위반이면 exit 1. 로컬 훅은 *내 세션의 편집*만 보므로, 동료가 git 으로 머지하는 PR 은 이 층이 막는다.
  규칙표 `--rules`      지금 걸려 있는 규칙을 표로. "뚫리면 규칙이 자란다"(25강) — 규칙은 여기 한 곳에만 둔다.

규칙은 지어낸 게 아니라 pension_qa 의 실제 import 구조에서 나왔다(app/*.py 의 import 줄):
  agent → guardrails · llm · retriever (조율자)   main → agent (진입점)   deploy_bot → mcp_client
  guardrails → re · dataclass (결정적 규칙 계층 — llm 을 부르면 "주민번호는 절대 안 흘린다"가 확률로 흔들린다, 11강)
  retriever → re · dataclass · pathlib (leaf)     llm → os · logging (확률적 계층, anthropic 은 함수 안 지연 import)

한계를 정직하게: grep 은 **텍스트에 보이는 것**만 잡는다. 두 줄로 나눈 `import importlib` / `importlib.import_module("app.llm")`,
`__import__`, 문자열 조립은 규칙 1 을 통과한다(2026-09-15 라이브 실측) — 그래서 규칙 4 가 동적 import 자체를 결정적 계층에서
금지한다. 그리고 훅은 Edit/Write 만 본다 — Bash 의 `sed -i`·`>>` 는 못 본다(파일 층이 잡는다). 벽이 아니라 층이다(14강).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 결정적 계층 = 확률적인 것(LLM·네트워크)을 부르면 안 되는 모듈. leaf = 위(agent·main)를 올려다보면 안 되는 모듈.
DETERMINISTIC = ("guardrails.py", "pension_calc.py")
LEAF = ("guardrails.py", "retriever.py", "llm.py", "pension_calc.py", "mcp_client.py")

_IMPORTS = r"^\s*(from\s+[\w.]*\b{name}\b|from\s+[\w.]+\s+import\s+[^#]*\b{name}\b|import\s+[^#]*\b{name}\b)"

RULES: list[dict] = [
    {
        "id": 1,
        "name": "레이어 위반",
        "targets": ("guardrails.py",),
        "pattern": _IMPORTS.format(name="llm"),
        "msg": "guardrails(결정적 계층)는 llm(확률적 계층)을 import 할 수 없다 — 안전장치가 확률로 오염된다",
        "since": "30강 규칙 1",
    },
    {
        "id": 2,
        "name": "의존 방향",
        "targets": LEAF,
        "pattern": _IMPORTS.format(name="(agent|main)"),
        "msg": "leaf 모듈은 agent·main 을 import 할 수 없다 — 순환 의존. 방향은 agent → leaf 뿐",
        "since": "30강 규칙 2",
    },
    {
        "id": 3,
        "name": "금지 import",
        "targets": DETERMINISTIC,
        "pattern": r"^\s*(from|import)\s+(requests|httpx|urllib3?|socket|aiohttp|anthropic|openai)\b",
        "msg": "결정적 계층에 네트워크·LLM 라이브러리가 들어올 수 없다",
        "since": "30강 규칙 3",
    },
]


def _rule_hits(basename: str, text: str) -> list[tuple[int, dict, str]]:
    """(줄번호, 규칙, 줄) — basename 에 걸리는 규칙만 본다. 줄 단위 grep 이라 들여쓰기(함수 안 지연 import)는 무관."""
    hits = []
    for rule in RULES:
        if basename not in rule["targets"]:
            continue
        rx = re.compile(rule["pattern"])
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append((i, rule, line.strip()))
    return hits


def check_hook(payload: dict) -> tuple[int, str]:
    """PreToolUse 입력 → (exit, stderr). 공식 hooks: tool_input.file_path 는 **절대 경로** — 상대 경로와 비교하면 영원히 안 걸린다."""
    tool_input = payload.get("tool_input") or {}
    basename = os.path.basename(str(tool_input.get("file_path", "")))
    content = tool_input.get("content") or tool_input.get("new_string") or ""
    hits = _rule_hits(basename, content)
    if not hits:
        return 0, ""
    _, rule, line = hits[0]
    return 2, f"아키텍처 가드 — {rule['name']}: {rule['msg']} ({rule['since']}) ← `{line}`"


def check_files(paths: list[Path]) -> list[str]:
    problems = []
    for p in paths:
        if not p.is_file():
            continue
        for lineno, rule, line in _rule_hits(p.name, p.read_text(encoding="utf-8")):
            problems.append(f"{p}:{lineno}: 🔴 Important — {rule['name']}: {rule['msg']} ({rule['since']}) ← `{line}`")
    return problems


def render_rules() -> str:
    out = [f"{'#':<3}{'규칙':<10}{'대상':<46}출처"]
    for r in RULES:
        out.append(f"{r['id']:<3}{r['name']:<10}{', '.join(r['targets']):<46}{r['since']}")
    out.append(f"규칙 {len(RULES)}개 — 뚫리면 여기에 한 줄 더 (25강: 규칙은 자란다)")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="아키텍처 가드 — 규칙을 두 층(훅·파일)에서 결정적으로 검사")
    ap.add_argument("paths", nargs="*", help="검사할 파일(파일 층). 없고 --hook 도 없으면 app/*.py 전부")
    ap.add_argument("--hook", action="store_true", help="PreToolUse 훅 모드: stdin JSON 의 들어올 내용을 검사, 위반 exit 2")
    ap.add_argument("--rules", action="store_true", help="규칙표 출력")
    args = ap.parse_args(argv)

    if args.rules:
        print(render_rules())
        return 0
    if args.hook:
        try:
            payload = json.load(sys.stdin)
        except Exception:
            return 0  # 훅 입력이 아니면 조용히 통과 — 단 '조용히'가 '안 도는'과 같아지지 않게 grade_final 이 exit 2 를 검사한다
        rc, msg = check_hook(payload)
        if msg:
            print(msg, file=sys.stderr)
        return rc
    paths = [Path(p) for p in args.paths] or sorted((ROOT / "app").glob("*.py"))
    problems = check_files(paths)
    for p in problems:
        print(p)
    print(f"아키텍처 검사 {len(paths)}파일 · 규칙 {len(RULES)}개 · 위반 {len(problems)}건" + (" → 긴급 큐(머지 차단, 27강 라우팅)" if problems else " ✓"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
