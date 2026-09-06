"""22강 — mock MCP 서버 계약 테스트. mcp SDK 없으면 건너뛴다.

도구 목록은 서버 객체에서 인프로세스로 열거한다(stdio 서브프로세스는 부하 시 응답 경쟁으로 flaky).
"""

import asyncio
import importlib

import pytest

pytest.importorskip("mcp", reason="pip install 'mcp>=2,<3'")

from pension_qa_docs import server


def _tool_names(mod):
    return sorted(t.name for t in asyncio.run(mod.mcp.list_tools()))


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


def test_default_server_is_read_only(monkeypatch):
    # 쓰기 도구의 부재로 읽기 전용을 지킨다 — 기본 argv엔 write 도구가 없다.
    monkeypatch.setattr("sys.argv", ["server"])
    importlib.reload(server)
    try:
        assert _tool_names(server) == ["list_docs", "read_doc"]
    finally:
        monkeypatch.setattr("sys.argv", ["server"])
        importlib.reload(server)


def test_with_write_switch_exposes_write_doc(monkeypatch):
    # 스코프 불일치 실습 스위치 — 서버가 write_doc 을 '내민다'.
    monkeypatch.setattr("sys.argv", ["server", "--with-write"])
    importlib.reload(server)
    try:
        assert "write_doc" in _tool_names(server)
    finally:
        monkeypatch.setattr("sys.argv", ["server"])
        importlib.reload(server)
