"""오케스트레이션: 입력 가드레일 → 마스킹 → 검색 → 근거 게이트 → LLM → 출력 가드레일.

각 단계는 아래 `ask()`에 순서대로 드러난다(SPEC.md·SPEC_score.md의 파이프라인 도식과 1:1).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import guardrails, llm, retriever

NO_DOCS_MESSAGE = "관련 근거 문서를 찾지 못해 답변하지 않습니다."

# 입력 가드레일 — 순서 유지(PII 먼저). 통과 못 하면 그 자리에서 차단한다.
_INPUT_CHECKS = (guardrails.check_input_pii, guardrails.check_input_scope)


@dataclass
class Result:
    answer: str
    sources: list[str] = field(default_factory=list)
    blocked: bool = False
    low_confidence: bool = False


def _blocked(reason: str, sources: list[str] | None = None) -> Result:
    """차단 응답도 근거 문서 이름은 채운다(CLAUDE.md 컨벤션·ADR 0002)."""
    return Result(reason, sources=sources or [], blocked=True)


def _guard_input(question: str) -> Result | None:
    """입력 가드레일 — 차단이면 `Result`, 통과면 `None`."""
    for check in _INPUT_CHECKS:
        verdict = check(question)
        if not verdict.ok:
            return _blocked(verdict.reason)
    return None


def ask(question: str) -> Result:
    rejected = _guard_input(question)
    if rejected:
        return rejected

    # 마스킹은 PII·범위 판정 뒤에(SPEC.md) — 마스킹된 문자열이 PII 패턴 판정을 흐리지 않게.
    # 이 지점 이후로 원문 질문은 흐르지 않는다: 검색·LLM 모두 마스킹본만 본다.
    masked_question = guardrails.mask_emails(question)

    found = retriever.search_scored(masked_question)
    if not found.docs:
        return _blocked(NO_DOCS_MESSAGE)

    names = [d.name for d in found.docs]

    # 근거 부실 게이트(ADR 0002) — 하드 미달이면 LLM을 부르지 않고 보류한다.
    evidence = guardrails.check_evidence(found.coverage)
    if evidence.level == guardrails.EVIDENCE_BLOCK:
        return _blocked(evidence.reason, names)

    raw = llm.answer(masked_question, [d.text for d in found.docs])

    leak = guardrails.check_output_leak(raw)
    if not leak.ok:
        return _blocked(leak.reason, names)

    return Result(
        guardrails.mask_emails(raw),
        sources=names,
        low_confidence=evidence.level == guardrails.EVIDENCE_LOW,
    )
