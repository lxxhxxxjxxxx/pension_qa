"""오케스트레이션: 입력 가드레일 → 검색 → 근거 게이트 → LLM → 출력 가드레일."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import guardrails, llm, retriever

NO_DOCS_REASON = "관련 근거 문서를 찾지 못해 답변하지 않습니다."


@dataclass
class Result:
    answer: str
    sources: list[str] = field(default_factory=list)
    blocked: bool = False
    low_confidence: bool = False


def ask(question: str) -> Result:
    """단계별 게이트를 차례로 통과시킨다. 각 단계는 차단 시 `Result`를 돌려주고 흐름을 끊는다."""
    refused = _guard_input(question)
    if refused:
        return refused

    # 입력 마스킹(ADR 0001 / SPEC.md) — PII·범위 체크를 통과한 뒤에 수행한다.
    # 순서를 바꾸면 마스킹된 문자열이 PII 판정을 흐린다. 이 지점 이후로 원문 질문은 흐르지 않는다.
    safe_question = guardrails.mask_emails(question)

    found = retriever.search_scored(safe_question)
    if not found.docs:
        return _refuse(NO_DOCS_REASON)

    names = [d.name for d in found.docs]

    # 근거 부실 게이트(ADR 0002) — 하드 미달이면 LLM을 부르지 않고 보류한다.
    evidence = guardrails.check_evidence(found.coverage)
    if evidence.level == guardrails.EVIDENCE_BLOCK:
        return _refuse(evidence.reason, names)

    return _answer(safe_question, found.docs, names, evidence.level)


def _guard_input(question: str) -> Result | None:
    """입력 가드레일(PII·범위). 통과하면 `None`."""
    for check in (guardrails.check_input_pii, guardrails.check_input_scope):
        verdict = check(question)
        if not verdict.ok:
            return _refuse(verdict.reason)
    return None


def _answer(question: str, docs: list[retriever.Doc], names: list[str], level: str) -> Result:
    """LLM 호출 + 출력 가드레일. 답변 경로는 항상 `sources`를 채운다(CLAUDE.md 컨벤션)."""
    raw = llm.answer(question, [d.text for d in docs])

    leak = guardrails.check_output_leak(raw)
    if not leak.ok:
        return _refuse(leak.reason, names)

    return Result(
        guardrails.mask_emails(raw),
        sources=names,
        low_confidence=level == guardrails.EVIDENCE_LOW,
    )


def _refuse(reason: str, names: list[str] | None = None) -> Result:
    """차단 응답 — 사유 문자열과, 알고 있다면 관련 문서 이름을 함께 돌려준다."""
    return Result(reason, sources=names or [], blocked=True)
