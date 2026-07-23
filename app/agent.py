"""오케스트레이션: 입력 가드레일 → 검색 → LLM → 출력 가드레일."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import guardrails, llm, retriever


@dataclass
class Result:
    answer: str
    sources: list[str] = field(default_factory=list)
    blocked: bool = False
    low_confidence: bool = False


def ask(question: str) -> Result:
    pii = guardrails.check_input_pii(question)
    if not pii.ok:
        return Result(pii.reason, blocked=True)

    scope = guardrails.check_input_scope(question)
    if not scope.ok:
        return Result(scope.reason, blocked=True)

    found = retriever.search_scored(question)
    docs = found.docs
    if not docs:
        return Result("관련 근거 문서를 찾지 못해 답변하지 않습니다.", blocked=True)

    names = [d.name for d in docs]

    # 근거 부실 게이트(ADR 0002) — 하드 미달이면 LLM을 부르지 않고 보류한다.
    evidence = guardrails.check_evidence(found.coverage)
    if evidence.level == guardrails.EVIDENCE_BLOCK:
        return Result(evidence.reason, sources=names, blocked=True)

    raw = llm.answer(question, [d.text for d in docs])

    leak = guardrails.check_output_leak(raw)
    if not leak.ok:
        return Result(leak.reason, sources=names, blocked=True)

    return Result(
        guardrails.mask_emails(raw),
        sources=names,
        low_confidence=evidence.level == guardrails.EVIDENCE_LOW,
    )
