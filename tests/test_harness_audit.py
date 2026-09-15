"""29강 — 자가점검 판정은 결정적이다(같은 레포·같은 로그 → 같은 판정)."""
from pathlib import Path

import pytest

from scripts import harness_audit as ha

FIX = Path(__file__).resolve().parent.parent / "scripts" / "mock_otel_console.log"
VERDICTS = {ha.OK, ha.WARN, ha.DEAD, ha.NA}


def test_여섯_칸이_전부_나온다():
    rows = ha.audit(None)
    assert [r["target"] for r in rows] == ["CLAUDE.md", "게이트", "스킬", "훅", "서브에이전트", "플러그인"]
    assert all(r["verdict"] in VERDICTS for r in rows)


def test_CLAUDE_md_의_없는_경로가_거짓말_줄로_잡힌다(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "guardrails.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("규칙은 `app/guardrails.py` 한 곳. 버전은 `plugins/x/.claude-plugin/plugin.json`.\n", encoding="utf-8")
    r = ha.audit_claude_md(tmp_path)
    assert r["verdict"] == ha.WARN and "plugins/x/.claude-plugin/plugin.json" in r["evidence"]


def test_CLAUDE_md_의_경로가_전부_실재하면_유효(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "guardrails.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("규칙은 `app/guardrails.py` 한 곳. 리포트는 `docs/runbook/x_*.md`(글롭은 대조 안 함).\n", encoding="utf-8")
    assert ha.audit_claude_md(tmp_path)["verdict"] == ha.OK


def test_훅은_전부_등록_실재_실행권한():
    assert ha.audit_hooks(None)["verdict"] == ha.OK


def test_플러그인은_드리프트_0():
    r = ha.audit_plugin()
    assert "드리프트 0" in r["evidence"]


def test_로그_없으면_스킬과_에이전트는_근거_없음():
    assert ha.audit_skills(None)["verdict"] == ha.NA
    assert ha.audit_agents(None)["verdict"] == ha.NA


def test_로그가_있으면_스킬_호출_수가_근거가_된다():
    from scripts import otel_log

    r = ha.audit_skills(otel_log.load(FIX))
    assert "code-review 1회" in r["evidence"]


def test_규칙_밖_모듈에서_항상_경고하는_게이트는_갱신_대상(monkeypatch):
    # llm.py 의 타임아웃 float 은 금액 계산이 아니다 — 여기서 경고하면 OK 분기에 영원히 못 간다(장식)
    monkeypatch.setattr(ha, "skill_gate_lines", lambda: ['grep -n "float(" app/llm.py || echo "OK: 금액 경로에 float 없음"'])
    r = ha.audit_gates()
    assert r["verdict"] == ha.WARN and "항상 경고" in r["evidence"]


def test_규칙_범위로_좁힌_게이트는_OK_분기에_도달한다(monkeypatch):
    monkeypatch.setattr(ha, "skill_gate_lines", lambda: ['grep -n "float(" app/pension_calc.py app/agent.py || echo "OK: 금액 경로에 float 없음"'])
    assert ha.audit_gates()["verdict"] == ha.OK


def test_렌더는_결정_필요_건수를_센다():
    text = ha.render([{"target": "x", "q": "q", "verdict": ha.WARN, "evidence": "e"}])
    assert "결정 필요: 1건" in text
