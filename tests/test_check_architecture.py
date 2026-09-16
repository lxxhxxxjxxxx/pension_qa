"""30강 — 아키텍처 가드는 결정적이다. 같은 줄이면 같은 판정, 두 층(훅·파일)이 같은 규칙.

2026-09-15 라이브 실측을 그대로 테스트로 박았다: 정적 import 는 잡히고, 함수 안 들여쓴 import 도 잡히고(줄 단위),
두 줄로 나눈 importlib 은 규칙 1 을 통과한다 — 그래서 규칙 4(동적 import 금지)가 생겼다. 훅 입력의 file_path 는 절대 경로다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_architecture as ca  # noqa: E402

ABS = "/home/someone/pension_qa/app/guardrails.py"


def _hook(basename_path: str, new_string: str) -> int:
    rc, _ = ca.check_hook({"tool_name": "Edit", "tool_input": {"file_path": basename_path, "old_string": "", "new_string": new_string}})
    return rc


def test_정적_import_는_훅이_막는다():
    assert _hook(ABS, "from . import llm\n") == 2
    assert _hook(ABS, "from . import guardrails, llm\n") == 2
    assert _hook(ABS, "from app.llm import ask\n") == 2
    assert _hook(ABS, "import app.llm as l\n") == 2


def test_함수_안_지연_import_도_잡힌다_줄_단위():
    """대본이 한때 '못 잡는다'고 했던 것 — grep 은 들여쓰기와 무관하다(2026-09-15 반증)."""
    assert _hook(ABS, "def f():\n    from . import llm\n    return llm\n") == 2


def test_무해한_편집은_통과():
    assert _hook(ABS, "import re\nfrom dataclasses import dataclass\n") == 0
    assert _hook(ABS, "# see notes from the llm docs\n") == 0  # 주석은 규칙 밖(줄머리 앵커)


def test_다른_파일은_규칙_1_대상이_아니다():
    assert _hook("/x/app/agent.py", "from . import guardrails, llm, retriever\n") == 0  # agent → llm 은 정상


def test_file_path_는_절대_경로라_basename_으로_본다():
    assert _hook("app/guardrails.py", "from . import llm\n") == 2
    assert _hook(ABS, "from . import llm\n") == 2


def test_의존_방향_leaf_가_agent_를_올려다보면_차단():
    assert _hook("/x/app/retriever.py", "from .agent import ask\n") == 2
    assert _hook("/x/app/retriever.py", "from . import agent\n") == 2
    assert _hook("/x/app/agent.py", "from . import retriever\n") == 0


def test_결정적_계층에_네트워크_라이브러리_차단():
    assert _hook(ABS, "import requests\n") == 2
    assert _hook("/x/app/pension_calc.py", "from anthropic import Anthropic\n") == 2
    assert _hook("/x/app/llm.py", "import anthropic\n") == 0  # llm 은 확률적 계층 — 허용


def test_두_줄_importlib_은_규칙_1_을_통과한다_변종의_실물():
    """규칙 4 가 없다면 통과한다 — 이 테스트는 '규칙 1 만으로는 못 잡는다'는 사실을 고정한다(규칙 4 는 grade_final ④ 가 본다)."""
    only_rule1 = [r for r in ca.RULES if r["id"] == 1]
    hits = [h for h in ca._rule_hits("guardrails.py", "import importlib\n_llm = importlib.import_module('app.llm')\n") if h[1] in only_rule1]
    assert hits == []


def test_파일_층은_실제_레포에서_위반_0(tmp_path):
    assert ca.check_files(sorted((ROOT / "app").glob("*.py"))) == []
    bad = tmp_path / "guardrails.py"
    bad.write_text("import re\nfrom . import llm\n", encoding="utf-8")
    problems = ca.check_files([bad])
    assert len(problems) == 1 and "레이어 위반" in problems[0] and ":2:" in problems[0]


def test_규칙표는_비어_있지_않고_출처가_있다():
    assert len(ca.RULES) >= 3 and all(r["since"].startswith("30강") for r in ca.RULES)
