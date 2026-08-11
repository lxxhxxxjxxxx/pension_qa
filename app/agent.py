"""오케스트레이션: 입력 가드레일 → 마스킹 → 검색 → 근거 게이트 → LLM → 출력 가드레일.

`ask()`는 SPEC.md·SPEC_score.md의 파이프라인 다이어그램과 1:1로 읽히도록 평평하게 둔다.
단계 함수는 "차단이면 `Result`, 통과면 `None`"을 돌려주고, 판정 로직 자체는 갖지 않는다 —
가드레일 판정은 `app/guardrails.py` 한 곳에만 있어야 한다(CLAUDE.md 컨벤션).
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


def _blocked(reason: str, sources: list[str] | None = None) -> Result:
    """차단 응답. 이유 문자열은 가드레일이 준 것을 그대로 쓴다(.claude/rules/guardrails.md)."""
    return Result(reason, sources=sources or [], blocked=True)


def _names(docs: list[retriever.Doc]) -> list[str]:
    return [d.name for d in docs]


def _guard_input(question: str) -> Result | None:
    """입력 가드레일 — 통과면 None. 새 입력 가드레일은 이 튜플에 추가한다."""
    for check in (guardrails.check_input_pii, guardrails.check_input_scope):
        verdict = check(question)
        if not verdict.ok:
            return _blocked(verdict.reason)
    return None


def _respond(question: str, docs: list[retriever.Doc], low_confidence: bool) -> Result:
    """LLM 호출 → 출력 가드레일 → 출력 마스킹. 어느 갈래로 나가든 근거 이름을 채운다."""
    sources = _names(docs)
    raw = llm.answer(question, [d.text for d in docs])

    leak = guardrails.check_output_leak(raw)
    if not leak.ok:
        return _blocked(leak.reason, sources)

    return Result(guardrails.mask_emails(raw), sources=sources, low_confidence=low_confidence)


def ask(question: str) -> Result:
    if (blocked := _guard_input(question)) is not None:
        return blocked

    # 입력 마스킹(SPEC.md) — PII·범위 체크를 통과한 뒤에 한다.
    # 순서를 바꾸면 마스킹된 문자열이 PII 패턴 판정을 흐린다.
    # 이 지점 이후로 원문 질문은 흐르지 않는다: 검색도 LLM도 마스킹본만 본다.
    question = guardrails.mask_emails(question)

    found = retriever.search_scored(question)
    if not found.docs:
        return _blocked(NO_DOCS_MESSAGE)

    # 근거 부실 게이트(ADR 0002·0003). 하드 미달이면 LLM을 부르지 않고 보류하되,
    # 사용자가 다음 행동을 잡을 수 있게 관련 문서 이름은 노출한다.
    evidence = guardrails.check_evidence(found.coverage)
    if evidence.level == guardrails.EVIDENCE_BLOCK:
        return _blocked(evidence.reason, _names(found.docs))

    return _respond(question, found.docs, evidence.level == guardrails.EVIDENCE_LOW)
