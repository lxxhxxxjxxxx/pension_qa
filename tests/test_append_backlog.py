"""27강 — 부채 큐 라우팅·백로그 병합이 결정적인지. 모델 없이 돈다.

리뷰 turn 은 확률적이지만, 그 산출이 어느 큐로 가고 백로그에 어떻게 쌓이는지는 규칙이다.
규칙이면 테스트할 수 있다 — 이것이 '결정적으로 만든다'의 실체다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import append_backlog as ab  # noqa: E402


@pytest.fixture(autouse=True)
def tmp_backlog(tmp_path, monkeypatch):
    """BACKLOG.md 를 임시 파일로 — 테스트가 레포 산출물을 건드리지 않게."""
    monkeypatch.setattr(ab, "BACKLOG", tmp_path / "BACKLOG.md")
    return ab.BACKLOG


def _row(file, line, severity, decision="폐기", verdict="-", note=""):
    return {
        "file": file,
        "line": line,
        "severity": severity,
        "decision": decision,
        "verdict": verdict,
        "note": note,
    }


def test_논파된_FP는_백로그에_오지_않는다():
    rows = [_row("app/retriever.py", 15, "Important", verdict="refuted", note="캐시 레이스")]
    assert ab.route(rows) == []


def test_confirm된_Important는_긴급큐라_백로그에_오지_않는다():
    rows = [_row("app/guardrails.py", 42, "Important", decision="confirm", verdict="survived")]
    assert ab.route(rows) == []


def test_confirm_안된_Nit은_부채큐로_간다():
    rows = [_row("app/retriever.py", 33, "Nit", note="변수명")]
    items = ab.route(rows)
    assert len(items) == 1 and items[0]["severity"] == "Nit"


def test_3조건_전부_충족이면_자동큐():
    conds = ab.three_conditions("app/retriever.py", "상위 k 기본값이 매직넘버 — 상수로")
    assert conds == {"저위험": True, "가역": True, "테스트격리": True}


def test_핵심모듈_변경은_사소해_보여도_사람큐():
    """guardrails 는 틀리면 사고다 — 저위험 조건에서 걸린다."""
    conds = ab.three_conditions("app/guardrails.py", "주석 추가")
    assert conds["저위험"] is False


def test_구조_변경은_가역_조건에서_걸린다():
    conds = ab.three_conditions("app/retriever.py", "캐시 도입 검토")
    assert conds["가역"] is False


def test_전용_테스트가_없으면_테스트격리_실패():
    """tests/test_main.py 가 없다 = 그 변경만 검증할 방법이 없다."""
    conds = ab.three_conditions("app/main.py", "주석 추가")
    assert conds["테스트격리"] is False


def test_같은_file_line은_병합되어_한_줄로_수렴한다():
    rows = [_row("app/retriever.py", 33, "Nit", note="변수명")]
    ab.merge_into_backlog(ab.route(rows))
    first = ab.BACKLOG.read_text(encoding="utf-8")
    for _ in range(9):
        ab.merge_into_backlog(ab.route(rows))
    assert ab.BACKLOG.read_text(encoding="utf-8") == first
    assert first.count("app/retriever.py:33") == 1


def test_갚은_항목의_체크상태는_보존된다():
    rows = [_row("app/retriever.py", 33, "Nit", note="변수명")]
    ab.merge_into_backlog(ab.route(rows))
    ab.BACKLOG.write_text(ab.BACKLOG.read_text(encoding="utf-8").replace("- [ ]", "- [x]"), encoding="utf-8")
    ab.merge_into_backlog(ab.route(rows))
    assert "- [x]" in ab.BACKLOG.read_text(encoding="utf-8")


def test_고정포맷이라_리뷰_리포트가_파싱된다():
    """자유 문장이면 자동 append 가 불가능하다 — 25강 포맷 제약이 여기서 자산이 된다."""
    text = (ROOT / "scripts" / "mock_review_report.md").read_text(encoding="utf-8")
    items = ab.parse_review_text(text)
    keys = {f"{i['file']}:{i['line']}" for i in items}
    assert "app/guardrails.py:42" not in keys  # 🔴 는 긴급 큐
    assert "app/main.py:9" in keys and "app/retriever.py:35" in keys
    assert {i["severity"] for i in items} == {"Nit", "Pre-existing"}


def test_입력_순서가_달라도_같은_백로그로_수렴한다():
    rows = [
        _row("app/retriever.py", 35, "Nit", note="매직넘버"),
        _row("app/main.py", 9, "Pre-existing", note="테스트 없음"),
    ]
    ab.merge_into_backlog(ab.route(rows))
    a = ab.BACKLOG.read_text(encoding="utf-8")
    ab.BACKLOG.unlink()
    ab.merge_into_backlog(ab.route(list(reversed(rows))))
    assert ab.BACKLOG.read_text(encoding="utf-8") == a
