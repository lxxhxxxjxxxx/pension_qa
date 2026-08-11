import pytest

from app import main as cli


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """키가 설정된 환경에서도 테스트가 실제 LLM 을 호출하지 않도록 stub 경로로 고정."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_cli_prints_usage_without_args(capsys):
    assert cli.main([]) == 1
    assert "사용법" in capsys.readouterr().out


def test_cli_prints_answer_sources_and_notes(capsys):
    code = cli.main(["연금저축", "세액공제", "한도는?", "회신은", "hong@corp.com", "으로"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("✅ ")
    assert "근거:" in out and "세액공제" in out
    assert "hong@corp.com" not in out
    assert "이메일 1건을 마스킹" in out


def test_cli_marks_blocked_answer(capsys):
    assert cli.main(["오늘", "점심", "메뉴", "추천해줘"]) == 0
    assert capsys.readouterr().out.startswith("⛔ ")
