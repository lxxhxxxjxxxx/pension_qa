"""20강 — llm.answer 신뢰성 하네스: 타임아웃 명시·분류 재시도·상한·Retry-After·폴백·로그."""

import logging

import pytest

from app import llm


class _Err(Exception):
    def __init__(self, status_code=None, retry_after=None):
        super().__init__(f"status={status_code}")
        self.status_code = status_code
        if retry_after is not None:
            self.response = type(
                "R", (), {"headers": {"retry-after": str(retry_after)}}
            )()


class _TimeoutErr(Exception):
    pass


def _client(outcomes, calls):
    """outcomes: 예외 인스턴스 또는 문자열(성공 답변) 목록. 호출마다 하나씩 소비."""

    class Messages:
        def create(self, **kw):
            calls.append(kw)
            out = outcomes.pop(0)
            if isinstance(out, Exception):
                raise out
            return type("M", (), {"content": [type("C", (), {"text": out})()]})()

    return type("Client", (), {"messages": Messages()})()


@pytest.fixture
def harness(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    calls, sleeps = [], []
    monkeypatch.setattr(llm, "_sleep", lambda s: sleeps.append(s))

    def use(outcomes):
        monkeypatch.setattr(llm, "_make_client", lambda: _client(list(outcomes), calls))
        return calls, sleeps

    return use


def test_stub_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm.answer("q", ["c"]).startswith("[LLM stub]")


def test_timeout_is_explicit(harness):
    calls, _ = harness(["ok"])
    llm.answer("q", ["c"])
    assert calls[0]["timeout"] == llm.TIMEOUT_S  # ① 기본값에 기대지 않는다


def test_retryable_then_success(harness):
    calls, sleeps = harness([_Err(503), "ok"])
    assert llm.answer("q", ["c"]) == "ok"
    assert len(calls) == 2 and len(sleeps) == 1


def test_timeout_is_retried(harness):
    calls, _ = harness([_TimeoutErr(), "ok"])
    assert llm.answer("q", ["c"]) == "ok"
    assert len(calls) == 2


def test_non_retryable_stops_immediately(harness):
    calls, sleeps = harness([_Err(401), "never"])
    out = llm.answer("q", ["c"])
    assert out.startswith(llm.FALLBACK_PREFIX)  # ④ 폴백
    assert len(calls) == 1 and sleeps == []  # ② 401은 재시도 안 함


def test_retry_cap_is_cost_cap(harness):
    calls, sleeps = harness([_Err(503)] * (llm.MAX_RETRIES + 5))
    out = llm.answer("q", ["c"])
    assert out.startswith(llm.FALLBACK_PREFIX)
    assert len(calls) == llm.MAX_RETRIES + 1  # ② 상한 = 비용 캡
    assert len(sleeps) == llm.MAX_RETRIES


def test_429_respects_retry_after(harness):
    _, sleeps = harness([_Err(429, retry_after=2), "ok"])
    assert llm.answer("q", ["c"]) == "ok"
    assert sleeps == [2.0]


def test_fallback_is_logged(harness, caplog):
    harness([_Err(401)])
    with caplog.at_level(logging.ERROR, logger="pension_qa.llm"):
        llm.answer("q", ["c"])
    assert any(
        "non-retryable" in r.message for r in caplog.records
    )  # ⑤ 조용히 넘기지 않는다
