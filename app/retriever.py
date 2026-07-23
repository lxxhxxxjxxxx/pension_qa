"""문서 검색 — 단순 토큰 겹침 스코어(임베딩 아님)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_token_re = re.compile(r"[가-힣A-Za-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _token_re.findall(text.lower())


@dataclass
class Doc:
    name: str
    text: str


def load_docs(data_dir: Path = DATA_DIR) -> list[Doc]:
    return [Doc(p.stem, p.read_text(encoding="utf-8")) for p in sorted(data_dir.glob("*.md"))]


@dataclass
class Retrieval:
    """검색 결과 + 근거 커버리지(ADR 0002 게이트 입력)."""

    docs: list[Doc]
    coverage: float


def search(query: str, k: int = 2, docs: list[Doc] | None = None) -> list[Doc]:
    return search_scored(query, k, docs).docs


def search_scored(query: str, k: int = 2, docs: list[Doc] | None = None) -> Retrieval:
    """점수를 버리지 않는 검색 경로 — 질문 토큰 대비 커버리지 비율을 함께 돌려준다.

    커버리지 = |질문 토큰 ∩ (상위 k 문서가 커버한 토큰)| / |질문 토큰|
    절대 겹침 개수가 아니라 비율인 이유: 질문이 길수록 겹침 개수가 자연히 커진다.
    """
    docs = docs if docs is not None else load_docs()
    q = set(_tokens(query))
    scored = []
    for d in docs:
        overlap = q & set(_tokens(d.text))
        scored.append((len(overlap), overlap, d))
    scored.sort(key=lambda x: x[0], reverse=True)

    top = [(overlap, d) for score, overlap, d in scored[:k] if score > 0]
    covered: set[str] = set()
    for overlap, _ in top:
        covered |= overlap
    coverage = len(covered) / len(q) if q else 0.0
    return Retrieval([d for _, d in top], coverage)
