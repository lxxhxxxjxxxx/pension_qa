"""오케스트레이션: 입력 가드레일 → 정제 → 검색 → LLM → 출력 가드레일.

`ask()` 는 단계 나열만 하고, 각 단계는 아래 `_stage_*` 함수가 담당한다.
차단은 예외가 아니라 `Result` 로 돌려주며, 어느 단계에서 멈췄는지를 `stage` 에 남긴다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from . import guardrails, llm, retriever

DEFAULT_K = 2
NO_EVIDENCE = "관련 근거 문서를 찾지 못해 답변하지 않습니다."


class Stage(str, Enum):
    INPUT_GUARD = "input_guard"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    OUTPUT_GUARD = "output_guard"


@dataclass(frozen=True)
class Source:
    name: str
    score: float


@dataclass
class Result:
    answer: str
    sources: list[Source] = field(default_factory=list)
    blocked: bool = False
    stage: Stage = Stage.GENERATION
    notes: list[str] = field(default_factory=list)

    @property
    def source_names(self) -> list[str]:
        return [s.name for s in self.sources]


def _stage_input_guard(question: str) -> Result | None:
    """차단이면 Result, 통과면 None."""
    for check in guardrails.INPUT_CHECKS:
        verdict = check(question)
        if not verdict.ok:
            return Result(verdict.reason, blocked=True, stage=Stage.INPUT_GUARD)
    return None


def _stage_sanitize(text: str, notes: list[str], where: str) -> str:
    clean = guardrails.sanitize(text)
    if clean.emails_masked:
        notes.append(f"{where}에서 이메일 {clean.emails_masked}건을 마스킹했습니다.")
    return clean.text


def _stage_retrieve(question: str, k: int) -> list[retriever.Hit]:
    return retriever.search_scored(question, k=k)


def _stage_output_guard(answer: str, sources: list[Source], notes: list[str]) -> Result:
    safe = _stage_sanitize(answer, notes, "출력")
    leak = guardrails.check_output_leak(safe)
    if not leak.ok:
        return Result(leak.reason, sources=sources, blocked=True, stage=Stage.OUTPUT_GUARD, notes=notes)
    return Result(safe, sources=sources, stage=Stage.GENERATION, notes=notes)


def ask(question: str, k: int = DEFAULT_K) -> Result:
    blocked = _stage_input_guard(question)
    if blocked is not None:
        return blocked

    notes: list[str] = []
    # 이메일은 차단이 아니라 마스킹 — 정제된 질문으로 검색·생성을 이어간다.
    safe_question = _stage_sanitize(question, notes, "입력")

    hits = _stage_retrieve(safe_question, k)
    if not hits:
        return Result(NO_EVIDENCE, blocked=True, stage=Stage.RETRIEVAL, notes=notes)

    sources = [Source(h.doc.name, round(h.score, 3)) for h in hits]
    raw = llm.answer(safe_question, [h.doc.text for h in hits])
    return _stage_output_guard(raw, sources, notes)
