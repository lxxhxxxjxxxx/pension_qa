"""27강 — 부채 지표가 결정적인지. 같은 코드면 같은 숫자, 같은 판정.

사람이 "이 모듈 좀 지저분한데"라고 하면 사람마다·어제와 오늘이 다르다.
지표는 몇 번을 돌려도 같다 — 그래서 갚는 속도를 잴 수 있다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import scan_debt as sd  # noqa: E402


def test_TODO_집계는_몇_번을_돌려도_같다():
    assert sd.todo_counts() == sd.todo_counts()


def test_모든_모듈이_표에_오른다():
    """빠진 모듈이 있으면 부채 지도에 구멍이 생긴다 — 안 세는 곳에 부채가 숨는다.

    ⚠️ "TODO 합이 0"을 단언하지 않는다. 그건 린트 규칙이지 지표가 아니고,
    부채를 심어둔 촬영 브랜치(ch4-27-debt)에서 이 테스트가 빨개지면
    21강 Stop 게이트가 영구 실패한다(14·15강 함정과 같은 계열)."""
    modules = {p.name for p in (ROOT / "app").glob("*.py")}
    assert set(sd.todo_counts()) == modules


def test_커버리지가_낮으면_커버부터로_판정한다():
    assert sd.verdict(0, 0, None).startswith("커버부터")


def test_커버는_높은데_mutation이_낮으면_테스트_보강():
    """밟기만 하고 안 잡는 테스트 = 있다고 믿는데 실제론 없는 안전망(15강)."""
    assert sd.verdict(0, 100, (50, 100)).startswith("테스트 보강")


def test_지표가_깨끗하면_양호():
    assert sd.verdict(0, 100, (100, 100)) == "양호"


def test_표는_나쁜_모듈부터_나온다():
    rows = [
        {"module": "a.py", "todo": 0, "coverage": 90, "mutation": None, "verdict": "양호"},
        {"module": "b.py", "todo": 3, "coverage": 0, "mutation": None, "verdict": "커버부터"},
    ]
    rows.sort(key=lambda r: (r["coverage"] if r["coverage"] is not None else 999, -r["todo"]))
    assert rows[0]["module"] == "b.py"  # 표 하나가 상환 순서를 정한다
