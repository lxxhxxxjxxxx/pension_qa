"""오케스트레이션: 입력 정제 → 입력 가드레일 → 검색 → LLM → 출력 가드레일."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import guardrails, llm, retriever


@dataclass
class Result:
    answer: str
    sources: list[str] = field(default_factory=list)
    blocked: bool = False


def ask(question: str) -> Result:
    # 정제를 가장 먼저 — 이후 단계는 모두 정제된 텍스트를 본다.
    # (제로폭 문자로 쪼갠 주민번호가 PII 검사를 통과하는 걸 막는다.)
    clean = guardrails.check_input_sanitize(question)
    if not clean.ok:
        return Result(clean.reason, blocked=True)
    question = clean.text

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
