"""오케스트레이션: 입력 정제·가드레일 → 검색 → LLM → 출력 가드레일."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import guardrails, llm, retriever


@dataclass
class Result:
    answer: str
    sources: list[str] = field(default_factory=list)
    blocked: bool = False


def ask(question: str) -> Result:
    # 이후 단계(PII·범위·검색·LLM)는 전부 정제된 질문만 본다.
    question, clean = guardrails.sanitize_input(question)
    if not clean.ok:
        return Result(clean.reason, blocked=True)

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

    return Result(raw, sources=[d.name for d in docs])
