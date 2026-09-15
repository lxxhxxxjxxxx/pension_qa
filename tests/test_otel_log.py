"""29강 — 텔레메트리 console 출력 파서. 픽스처는 2.1.272 실측 원본(식별자만 가림)."""
from pathlib import Path

from scripts import otel_log

FIX = Path(__file__).resolve().parent.parent / "scripts" / "mock_otel_console.log"


def _data():
    return otel_log.load(FIX)


def test_문서에_없는_이벤트가_실제로_찍힌다():
    names = {e["name"] for e in _data()["events"]}
    # 공식 이벤트 표(2026-09-15)엔 없지만 출력엔 있다 — 문서가 아니라 출력을 믿는다
    assert {"skill_activated", "hook_registered", "mcp_server_connection", "tool_decision"} <= names


def test_skill_activated_는_스킬_이름을_들고_있다():
    assert otel_log.count_events(_data(), "skill_activated", "skill.name") == {"code-review": 1}


def test_hook_registered_는_settings_의_이벤트별_훅_수와_같다():
    reg = otel_log.count_events(_data(), "hook_registered", "hook_event")
    assert reg == {"PostToolUse": 1, "PreToolUse": 4, "Stop": 2, "ConfigChange": 1}


def test_비용_메트릭은_스킬별로_합산된다():
    by = otel_log.sum_metric(_data(), "cost.usage", "skill.name")
    assert set(by) == {"code-review"} and by["code-review"] > 0


def test_토큰_메트릭은_type_별로_나뉜다():
    tok = otel_log.sum_metric(_data(), "token.usage", "type")
    assert {"input", "output", "cacheRead", "cacheCreation"} <= set(tok)
