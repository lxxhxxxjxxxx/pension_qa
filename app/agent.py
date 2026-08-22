"""오케스트레이션: 입력 가드레일 → 검색 → LLM → 출력 가드레일."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import guardrails, llm, retriever


@dataclass
class Result:
    answer: str
    sources: list[str] = field(default_factory=list)
    blocked: bool = False


# 같은 질문이 반복되면 검색·LLM 호출을 건너뛴다(응답 지연·API 비용 절감).
_ANSWER_CACHE: dict[str, Result] = {}


def ask(question: str) -> Result:
    cached = _ANSWER_CACHE.get(question)
    if cached is not None:
        return cached

    pii = guardrails.check_input_pii(question)
    if not pii.ok:
        return Result(pii.reason, blocked=True)

    scope = guardrails.check_input_scope(question)
    if not scope.ok:
        return Result(scope.reason, blocked=True)

    docs = retriever.search(question)
    if not docs:
        return Result("관련 근거 문서를 찾지 못해 답변하지 않습니다.", blocked=True)

    raw = llm.answer(question, [d.text for d in docs])

    leak = guardrails.check_output_leak(raw)
    if not leak.ok:
        return Result(leak.reason, sources=[d.name for d in docs], blocked=True)

    result = Result(raw, sources=[d.name for d in docs])
    _ANSWER_CACHE[question] = result
    return result
