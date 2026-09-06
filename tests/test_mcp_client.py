"""22강 — MCP 신뢰성 래퍼(app/mcp_client.py) 테스트. 실제 서버 불요(invoke 주입)."""

from app import mcp_client as m


def _invoker(seq):
    calls = {"n": 0}

    def invoke(tool, args, *, timeout):
        i = calls["n"]
        calls["n"] += 1
        r = seq[i]
        if isinstance(r, Exception):
            raise r
        return r

    return invoke, calls


def test_success_first_try():
    invoke, calls = _invoker(["ok"])
    assert m.call_mcp(invoke, "read_doc", {}, _sleep=lambda s: None) == "ok"
    assert calls["n"] == 1


def test_503_then_success_within_cap():
    invoke, calls = _invoker([m.MCPHTTPError(503), "ok"])
    assert m.call_mcp(invoke, "read_doc", {}, _sleep=lambda s: None) == "ok"
    assert calls["n"] == 2


def test_timeout_is_retried():
    invoke, calls = _invoker([m.MCPTimeout(), m.MCPTimeout(), "ok"])
    assert m.call_mcp(invoke, "read_doc", {}, _sleep=lambda s: None) == "ok"
    assert calls["n"] == 3


def test_401_stops_immediately_to_fallback():
    invoke, calls = _invoker([m.MCPHTTPError(401), "never"])
    r = m.call_mcp(invoke, "read_doc", {}, _sleep=lambda s: None)
    assert isinstance(r, m.Unavailable)  # 재시도 금지 → 폴백
    assert calls["n"] == 1


def test_retry_cap_is_max_retries_plus_one():
    invoke, calls = _invoker([m.MCPHTTPError(503)] * 10)
    r = m.call_mcp(invoke, "read_doc", {}, max_retries=3, _sleep=lambda s: None)
    assert isinstance(r, m.Unavailable)
    assert calls["n"] == 4  # 상한 = 비용 캡


def test_fallback_prefers_stale_cache():
    invoke, _ = _invoker([m.MCPTimeout()] * 5)
    r = m.call_mcp(
        invoke,
        "read_doc",
        {},
        max_retries=1,
        cache_get=lambda t: "stale",
        _sleep=lambda s: None,
    )
    assert r == "stale"  # 캐시 있으면 보수적 실패 대신 stale


def test_is_write_tool():
    assert m.is_write_tool("mcp__pension_qa-docs__write_doc")
    assert not m.is_write_tool("mcp__pension_qa-docs__read_doc")
