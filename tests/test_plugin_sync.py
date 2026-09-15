"""28강 — 플러그인은 `.claude/` 하네스의 결정적 사본이어야 한다.

손으로 복사한 플러그인은 `.claude/` 를 고친 날 조용히 낡는다(드리프트). 그래서 사본을 스크립트로 만들고,
"지금 `.claude/` 로 다시 만들면 커밋된 플러그인과 같은가"를 테스트가 묻는다. 29강 자가점검의 첫 항목.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_plugin as bp  # noqa: E402

PLUGIN = ROOT / "plugins" / "ai-product-harness"
MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"


def test_플러그인은_claude_와_동일하다():
    """드리프트 0 — `.claude/` 를 고쳤으면 `python3 scripts/build_plugin.py` 를 다시 돌려야 한다."""
    assert bp.check() == []


def test_claude_plugin_안엔_plugin_json_만():
    """사고 1 — skills/·agents/·hooks/ 를 .claude-plugin/ 안에 두면 조용히 로드가 안 된다(validate 도 못 잡는다)."""
    inside = sorted(p.name for p in (PLUGIN / ".claude-plugin").iterdir())
    assert inside == ["plugin.json"]
    for d in ("skills", "agents", "hooks", "output-styles", "commands"):
        assert (PLUGIN / d).is_dir(), f"{d}/ 는 플러그인 루트에 있어야 한다"


def test_hooks_json_은_플러그인_루트_경로만_쓴다():
    """settings 의 hooks 를 '그대로' 옮기면 다른 레포에선 .claude/hooks/ 가 없어 전부 실패한다."""
    text = (PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8")
    assert ".claude/hooks" not in text
    data = json.loads(text)
    assert set(data) == {"hooks"}, "플러그인 hooks.json 은 {\"hooks\": {...}} 한 겹"
    referenced = re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}\\?"?/hooks/([\w.-]+\.sh)', text)
    assert referenced, "훅 스크립트 참조가 하나도 없다"
    for sh in referenced:
        assert (PLUGIN / "hooks" / sh).exists(), f"hooks/{sh} 가 플러그인에 없다"


def test_레포_몫은_플러그인에_없다():
    """CLAUDE.md·rules·permissions·env 는 플러그인이 나르지 못한다 — 두 축을 섞으면 '설치했는데 게이트가 없다'가 된다."""
    assert not (PLUGIN / "CLAUDE.md").exists()
    assert not (PLUGIN / "rules").exists()
    settings = PLUGIN / "settings.json"
    if settings.exists():
        keys = set(json.loads(settings.read_text(encoding="utf-8")))
        assert keys <= {"agent", "subagentStatusLine"}


def test_마켓_카탈로그는_실재_플러그인을_가리킨다():
    """카탈로그 이름 ↔ 매니페스트 이름이 같아야 `/plugin install name@pension_qa-team` 이 그 폴더를 찾는다."""
    mkt = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert mkt["name"] == "pension_qa-team"
    entry = next(p for p in mkt["plugins"] if p["name"] == "ai-product-harness")
    src = ROOT / entry["source"]
    assert (src / ".claude-plugin" / "plugin.json").exists()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["name"] == entry["name"]


def test_버전이_명시돼_있다():
    """version 을 박아 두면 bump 전엔 아무도 새 버전을 못 받는다 — 그래서 값이 있어야 하고 semver 여야 한다."""
    v = json.loads(MANIFEST.read_text(encoding="utf-8")).get("version")
    assert v and re.fullmatch(r"\d+\.\d+\.\d+", v), v


def test_MCP_서버는_플러그인과_함께_움직인다():
    """다른 레포에서 켜져도 서버 모듈과 문서가 있어야 한다 — PYTHONPATH 가 플러그인 안을 가리킨다."""
    mcp = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
    for cfg in mcp["mcpServers"].values():
        assert cfg["env"]["PYTHONPATH"] == "${CLAUDE_PLUGIN_ROOT}/servers"
    assert (PLUGIN / "servers" / "pension_qa_docs" / "server.py").exists()
    assert list((PLUGIN / "servers" / "data").glob("*.md"))
