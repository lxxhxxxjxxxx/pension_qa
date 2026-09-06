"""22강 — mock MCP 서버 계약 테스트. mcp SDK 없으면 건너뛴다."""

import importlib
import subprocess
import sys

import pytest

pytest.importorskip("mcp", reason="pip install 'mcp>=2,<3'")

server = importlib.import_module("pension_qa_docs.server")


def test_list_docs_returns_three_stems():
    assert server._list_docs() == [
        "IRP_수령요건",
        "연금소득세_과세",
        "연금저축_세액공제",
    ]


def test_read_doc_reads_existing():
    assert "세액공제" in server._read_doc("연금저축_세액공제")


def test_read_doc_missing_raises_404_sense():
    # 틀린 이름(정답 IRP_수령요건) → 서버는 살아서 에러까지 냈다(404 감각, 연결 실패와 다름)
    with pytest.raises(FileNotFoundError):
        server._read_doc("IRP_수령조건")


def _tools_via_handshake(*extra_args):
    reqs = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
        '{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}\n'
        '{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
        '{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n'
    )
    out = subprocess.run(
        [sys.executable, "-m", "pension_qa_docs.server", *extra_args],
        input=reqs,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout
    import json

    for line in out.splitlines():
        d = json.loads(line)
        if d.get("id") == 2:
            return sorted(t["name"] for t in d["result"]["tools"])
    return []


def test_default_server_is_read_only():
    # 쓰기 도구의 부재로 읽기 전용을 지킨다 — write 도구가 노출되지 않는다.
    assert _tools_via_handshake() == ["list_docs", "read_doc"]


def test_with_write_switch_exposes_write_doc():
    # 스코프 불일치 실습 스위치 — 서버가 write_doc 을 '내민다'.
    assert "write_doc" in _tools_via_handshake("--with-write")
