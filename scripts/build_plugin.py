#!/usr/bin/env python3
"""28강 — `.claude/` 하네스를 플러그인 `plugins/ai-product-harness/` 로 결정적으로 패키징한다.

왜 스크립트인가: 손으로 복사하면 `.claude/` 를 고친 뒤 플러그인을 안 고치는 날이 온다(드리프트).
같은 입력이면 같은 출력 — `--check` 가 커밋된 플러그인과 지금 `.claude/` 가 같은지 판정한다(테스트·CI).

들어가는 것(공식 plugins 구조)            나가지 않는 것(레포 몫)
  .claude/skills/        → skills/           CLAUDE.md · .claude/rules/ · memory   (레포 컨텍스트)
  .claude/agents/        → agents/           settings.json 의 permissions · env      (플러그인 settings.json 은
  .claude/output-styles/ → output-styles/                                              agent·subagentStatusLine 만)
  .claude/commands/      → commands/
  .claude/hooks/*.sh     → hooks/*.sh
  settings.json["hooks"] → hooks/hooks.json   경로 "$CLAUDE_PROJECT_DIR"/.claude/hooks/ → "${CLAUDE_PLUGIN_ROOT}"/hooks/
  .mcp.json              → .mcp.json          서버 모듈·data 를 servers/ 로 같이 싣고 PYTHONPATH 로 가리킨다
  pension_qa_docs/, data/ → servers/

매니페스트 `.claude-plugin/plugin.json` 은 손으로 쓴다(version bump 가 거기서 일어난다). 이 스크립트는 건드리지 않는다.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".claude"
PLUGIN = ROOT / "plugins" / "ai-product-harness"

PROJECT_HOOK_PREFIX = '"$CLAUDE_PROJECT_DIR"/.claude/hooks/'
PLUGIN_HOOK_PREFIX = '"${CLAUDE_PLUGIN_ROOT}"/hooks/'

COPY_DIRS = {  # .claude/<src> → plugin/<dst>
    "skills": "skills",
    "agents": "agents",
    "output-styles": "output-styles",
    "commands": "commands",
}
SERVER_DIRS = ["pension_qa_docs", "data"]  # MCP 서버가 플러그인과 함께 움직이도록
KEEP_AT_ROOT = [".claude-plugin", "README.md"]  # 빌드가 건드리지 않는 것


def _copytree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".gate", "*.log"))


def build(out: Path) -> dict:
    """`.claude/` → out. 무엇을 넣고 뺐는지 표로 돌려준다."""
    report = {"in": [], "out": []}
    for name in list(out.iterdir()) if out.exists() else []:
        if name.name not in KEEP_AT_ROOT:
            shutil.rmtree(name) if name.is_dir() else name.unlink()
    out.mkdir(parents=True, exist_ok=True)

    for src_name, dst_name in COPY_DIRS.items():
        src = SRC / src_name
        if src.is_dir():
            _copytree(src, out / dst_name)
            report["in"].append(f".claude/{src_name}/ → {dst_name}/")

    hooks_dir = out / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    for sh in sorted((SRC / "hooks").glob("*.sh")):
        shutil.copy2(sh, hooks_dir / sh.name)
    settings = json.loads((SRC / "settings.json").read_text(encoding="utf-8"))
    hooks = settings.get("hooks", {})
    for groups in hooks.values():  # 이벤트 → [{matcher, hooks:[{command}]}]
        for group in groups:
            for h in group.get("hooks", []):
                if "command" in h:
                    h["command"] = h["command"].replace(PROJECT_HOOK_PREFIX, PLUGIN_HOOK_PREFIX)
    hooks_json = json.dumps({"hooks": hooks}, ensure_ascii=False, indent=2)
    (hooks_dir / "hooks.json").write_text(hooks_json + "\n", encoding="utf-8")
    report["in"].append("settings.json[hooks] + .claude/hooks/*.sh → hooks/ (경로 ${CLAUDE_PLUGIN_ROOT})")
    for key in ("permissions", "env"):
        if key in settings:
            report["out"].append(f"settings.json[{key}] — 레포 몫(플러그인 settings.json 은 agent·subagentStatusLine 만)")

    mcp_src = ROOT / ".mcp.json"
    if mcp_src.exists():
        mcp = json.loads(mcp_src.read_text(encoding="utf-8"))
        servers = out / "servers"
        servers.mkdir(exist_ok=True)
        for d in SERVER_DIRS:
            if (ROOT / d).is_dir():
                _copytree(ROOT / d, servers / d)
        for cfg in mcp.get("mcpServers", {}).values():
            cfg.setdefault("env", {})["PYTHONPATH"] = "${CLAUDE_PLUGIN_ROOT}/servers"
        (out / ".mcp.json").write_text(json.dumps(mcp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report["in"].append(".mcp.json + pension_qa_docs/ + data/ → .mcp.json · servers/ (PYTHONPATH=${CLAUDE_PLUGIN_ROOT}/servers)")

    for name in ("rules",):
        if (SRC / name).exists():
            report["out"].append(f".claude/{name}/ — 레포 컨텍스트(CLAUDE.md 와 함께 clone 으로 온다)")
    report["out"].append("CLAUDE.md · memory — 레포 컨텍스트")
    return report


def diff(a: Path, b: Path) -> list[str]:
    """두 트리의 차이를 상대경로 목록으로. 비어 있으면 동일."""
    out: list[str] = []

    def walk(da: Path, db: Path, rel: str) -> None:
        cmp = filecmp.dircmp(da, db, ignore=["__pycache__", ".claude-plugin", "README.md"])
        out.extend(f"{rel}{x} (플러그인에만)" for x in cmp.left_only)
        out.extend(f"{rel}{x} (.claude 에만)" for x in cmp.right_only)
        out.extend(f"{rel}{x} (내용 다름)" for x in cmp.diff_files)
        for sub in cmp.common_dirs:
            walk(da / sub, db / sub, f"{rel}{sub}/")

    walk(a, b, "")
    return out


def check() -> list[str]:
    """커밋된 플러그인 ↔ 지금 `.claude/` 로 빌드한 결과. 다르면 드리프트 목록."""
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "fresh"
        build(fresh)
        return diff(PLUGIN, fresh)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="빌드하지 않고 커밋된 플러그인과 .claude/ 의 드리프트만 판정(exit 1)")
    args = ap.parse_args(argv)
    if args.check:
        drift = check()
        if drift:
            print("✘ 드리프트 — .claude/ 를 고쳤으면 `python3 scripts/build_plugin.py` 로 플러그인을 다시 만들 것:")
            for d in drift:
                print(f"  - {d}")
            return 1
        print("✔ plugins/ai-product-harness == .claude/ (드리프트 없음)")
        return 0
    report = build(PLUGIN)
    print(f"✔ built {PLUGIN.relative_to(ROOT)}/")
    for line in report["in"]:
        print(f"  + {line}")
    for line in report["out"]:
        print(f"  - {line}")
    manifest = PLUGIN / ".claude-plugin" / "plugin.json"
    if manifest.exists():
        v = json.loads(manifest.read_text(encoding="utf-8")).get("version", "(없음)")
        print(f"  version {v} — 팀에 퍼뜨리려면 .claude-plugin/plugin.json 의 version 을 올릴 것")
    return 0


if __name__ == "__main__":
    sys.exit(main())
