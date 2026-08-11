"""오케스트레이션: 입력 가드레일 → 입력 마스킹 → 검색 → 근거 게이트 → LLM → 출력 가드레일.

`ask()`는 SPEC.md·SPEC_score.md의 파이프라인 다이어그램을 그대로 읽히게 두고,
각 단계는 "차단이면 `Result`, 통과면 `None`"을 돌려주는 작은 함수로 분리했다.
차단 응답은 전부 `_blocked()`를 거치게 해서 `sources`를 채우는 컨벤션(CLAUDE.md)이
경로마다 흩어지지 않게 한다. 판정 로직 자체는 `guardrails.py`에만 있다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import guardrails, llm, retriever

NO_DOCS_MESSAGE = "관련 근거 문서를 찾지 못해 답변하지 않습니다."


@dataclass
class Result:
    answer: str
    sources: list[str] = field(default_factory=list)
    blocked: bool = False
    low_confidence: bool = False


def ask(question: str) -> Result:
    rejected = _screen_input(question)
    if rejected is not None:
        return rejected

    # 입력 마스킹(SPEC.md) — PII·범위 체크를 통과한 뒤에.
    # 이 지점 이후로 원문 질문은 검색에도 LLM에도 흐르지 않는다.
    masked = guardrails.mask_emails(question)

    retrieval = retriever.search_scored(masked)
    if not retrieval.docs:
        return _blocked(NO_DOCS_MESSAGE)

    # 근거 부실 게이트(ADR 0002) — 하드 미달이면 LLM을 부르지 않고 보류한다.
    # 보류해도 관련 문서 이름은 노출한다.
    evidence = guardrails.check_evidence(retrieval.coverage)
    if evidence.level == guardrails.EVIDENCE_BLOCK:
        return _blocked(evidence.reason, _sources(retrieval))

    return _respond(masked, retrieval, evidence)


def _screen_input(question: str) -> Result | None:
    """입력 가드레일 — PII 차단 후 범위 판정. 순서가 사유 문자열의 우선순위다."""
    for check in (guardrails.check_input_pii(question), guardrails.check_input_scope(question)):
        if not check.ok:
            return _blocked(check.reason)
    return None


def _respond(
    question: str, retrieval: retriever.Retrieval, evidence: guardrails.EvidenceCheck
) -> Result:
    """LLM 호출 → 출력 가드레일(유출 차단 → 이메일 마스킹)."""
    raw = llm.answer(question, [d.text for d in retrieval.docs])

    leak = guardrails.check_output_leak(raw)
    if not leak.ok:
        return _blocked(leak.reason, _sources(retrieval))

    return Result(
        guardrails.mask_emails(raw),
        sources=_sources(retrieval),
        low_confidence=evidence.level == guardrails.EVIDENCE_LOW,
    )


def _sources(retrieval: retriever.Retrieval) -> list[str]:
    return [d.name for d in retrieval.docs]


def _blocked(reason: str, sources: list[str] | None = None) -> Result:
    return Result(reason, sources=sources or [], blocked=True)
