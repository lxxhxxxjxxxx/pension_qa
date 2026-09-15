"""pension_qa 읽기 전용 문서 MCP 서버 (22강 · 미니 mock).

data/ 의 연금 문서를 읽기 전용으로 노출한다. 쓰기 도구는 기본적으로 존재하지 않는다 —
읽기 전용을 플래그가 아니라 '쓰기 도구의 부재'로 지킨다(18강 스코프 안티패턴 방어, 코드가 곧 정책).

사전 준비: pip install "mcp>=2,<3"   (촬영 실측 2026-09-06: mcp 2.1.1)
  ⚠️ mcp 2.x에서 FastMCP → MCPServer 로 이름이 바뀌었다. 아래 import가 두 버전 모두를 받는다.
실행: python3 -m pension_qa_docs.server   (기본 stdio transport · 촬영 PC엔 python 없음 → python3)
실습 스위치: --slow(startup 5초 지연 = 타임아웃 유발) · --with-write(쓰기 도구 노출 = 스코프 불일치)
"""

import sys
import time
from pathlib import Path

try:
    from mcp.server.mcpserver import MCPServer as _Server  # mcp >= 2
except ImportError:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP as _Server  # mcp < 2

mcp = _Server("pension_qa-docs")
DATA = (
    Path(__file__).resolve().parent.parent / "data"
)  # 연금저축_세액공제·IRP_수령요건·연금소득세_과세


def _list_docs() -> list[str]:
    """data/ 연금 문서 목록(확장자 제외)을 정렬해 돌려준다."""
    return sorted(p.stem for p in DATA.glob("*.md"))


def _read_doc(name: str) -> str:
    """연금 문서 하나를 이름으로 읽는다. 없는 이름 → FileNotFoundError.

    '서버는 살아서 대답까지 했다'는 404 감각 — 연결 실패(✘)와 다른 신호(20강).
    """
    path = DATA / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"문서 없음: {name}")
    return path.read_text(encoding="utf-8")


@mcp.tool()
def list_docs() -> list[str]:
    """data/ 연금 문서 목록을 돌려준다(읽기 전용)."""
    return _list_docs()


@mcp.tool()
def read_doc(name: str) -> str:
    """연금 문서 하나를 이름으로 읽는다. 없으면 에러."""
    return _read_doc(name)


# 쓰기 도구는 기본적으로 '존재하지 않는다' — 코드가 곧 읽기 전용 정책.
if "--with-write" in sys.argv:  # §3 (5) 스코프 불일치 실습용 스위치

    @mcp.tool()
    def write_doc(name: str, content: str) -> str:
        """(실습용) 서버가 갑자기 '내미는' 쓰기 도구 — 우리 정책 밖 범위."""
        return "실습용 스텁 — 실제로 저장하지 않음"


if __name__ == "__main__":
    if "--slow" in sys.argv:  # §3 (2) 타임아웃 실습용: 일부러 늦게 뜬다
        time.sleep(5)
    mcp.run()  # 기본 stdio transport
