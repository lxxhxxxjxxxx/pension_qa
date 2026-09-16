"""30강 — 상환 기록은 멱등·결정적이고, 사람 큐 항목은 에이전트가 갚을 수 없다."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import record_repayment_adr as rr  # noqa: E402

BACKLOG = """# 부채 백로그 (자동 축적)

## 자동 큐 — 3조건 전부 충족 (에이전트가 상환)

- [ ] 🟡 Nit · app/retriever.py:35 · 상위 k 기본값 2 가 매직넘버 · 저위험✓ 가역✓ 테스트격리✓

## 사람 큐 — 3조건 중 미충족 있음

- [ ] 🟣 Pre-existing · app/main.py:9 · CLI 진입 경로에 테스트가 없다 · 저위험✗ 가역✓ 테스트격리✗

## 지표 — scan_debt 가 흘려보낸 것

- (없음)
"""


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "0014-x.md").write_text("# ADR 0014\n", encoding="utf-8")
    (tmp_path / "BACKLOG.md").write_text(BACKLOG, encoding="utf-8")
    return tmp_path


def test_자동_큐_항목은_ADR_다음_번호로_기록되고_백로그가_체크된다(repo):
    p = rr.record("app/retriever.py:35", "abc1234", "검문 5/5", adr_dir=repo / "docs" / "adr", backlog=repo / "BACKLOG.md", today="2026-09-16")
    assert p.name == "0015-repay-retriever-35.md"
    text = p.read_text(encoding="utf-8")
    assert "abc1234" in text and "저위험✓ 가역✓ 테스트격리✓" in text and "검문 5/5" in text
    assert "- [x] 🟡 Nit · app/retriever.py:35" in (repo / "BACKLOG.md").read_text(encoding="utf-8")


def test_두_번_기록해도_ADR_은_하나(repo):
    a = rr.record("app/retriever.py:35", "abc1234", "검문 5/5", adr_dir=repo / "docs" / "adr", backlog=repo / "BACKLOG.md")
    b = rr.record("app/retriever.py:35", "zzz9999", "검문 5/5", adr_dir=repo / "docs" / "adr", backlog=repo / "BACKLOG.md")
    assert a == b and len(list((repo / "docs" / "adr").glob("*-repay-*"))) == 1


def test_사람_큐_항목은_거부(repo):
    with pytest.raises(SystemExit, match="사람 큐"):
        rr.record("app/main.py:9", "abc1234", "검문 5/5", adr_dir=repo / "docs" / "adr", backlog=repo / "BACKLOG.md")


def test_백로그_밖_항목은_거부(repo):
    with pytest.raises(SystemExit, match="BACKLOG"):
        rr.record("app/nowhere.py:1", "abc1234", "검문 5/5", adr_dir=repo / "docs" / "adr", backlog=repo / "BACKLOG.md")


def test_ADR_번호는_기존_최대_다음(repo):
    assert rr.next_number(repo / "docs" / "adr") == 15
