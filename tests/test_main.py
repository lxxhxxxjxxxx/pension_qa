"""CLI 스모크 — 렌더링까지 포함한 전 구간(입력 마스킹 → 검색 → stub 답변 → 출력 마스킹)."""
from app.main import main


def test_cli_prints_usage_without_question(capsys):
    assert main([]) == 1
    assert "사용법" in capsys.readouterr().out


def test_cli_masks_email_and_prints_sources(capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["연금저축 세액공제 한도가 얼마인가요? 회신은 hong@example.com 으로"]) == 0

    out = capsys.readouterr().out
    assert "hong@example.com" not in out  # LLM stub이 질문을 되풀이해도 원문은 안 나온다
    assert "h***@e***.com" in out
    assert "근거: 연금저축_세액공제" in out
