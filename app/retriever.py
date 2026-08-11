"""문서 검색 — 토큰 겹침 기반 점수(임베딩 아님).

랭킹은 BM25 계열이다: 희소 토큰에 IDF 가중치를 주고 문서 길이로 정규화한다.
겹침 **개수**만 세던 이전 방식은 모든 문서에 나오는 `연금` 한 번과 한 문서에만 나오는
`세액공제` 한 번을 똑같이 취급해, 변별력 없는 토큰이 순위를 흔들었다.

근거 게이트(ADR 0002)가 먹는 **커버리지 정의는 가중치 없는 원래 비율 그대로** 둔다 —
임계값 0.15/0.40이 그 정의로 캘리브레이션돼 있기 때문. 가중치는 순위에만 쓴다.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_token_re = re.compile(r"[가-힣A-Za-z0-9]+")

# BM25 파라미터 — 표준 기본값.
_K1 = 1.5  # 용어 빈도 포화 계수: 같은 토큰이 반복돼도 점수가 무한히 오르지 않게 한다
_B = 0.75  # 문서 길이 정규화 강도: 긴 문서가 분량만으로 이기지 않게 한다


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


def _idf(term: str, doc_sets: list[set[str]]) -> float:
    """BM25 IDF. `log(1 + …)` 형태라 항상 양수 —

    덕분에 `score > 0`은 이전 구현과 똑같이 "질문 토큰이 최소 하나 등장"을 뜻한다.
    (표준 형태는 흔한 토큰에서 음수가 되어 이 등가성이 깨진다.)
    """
    n = sum(1 for s in doc_sets if term in s)
    return math.log(1 + (len(doc_sets) - n + 0.5) / (n + 0.5))


def _bm25(
    q: set[str],
    counts: Counter[str],
    length: int,
    avg_len: float,
    idf: dict[str, float],
) -> float:
    score = 0.0
    for term in q:
        tf = counts.get(term, 0)
        if not tf:
            continue
        score += idf[term] * tf * (_K1 + 1) / (tf + _K1 * (1 - _B + _B * length / avg_len))
    return score


def search(query: str, k: int = 2, docs: list[Doc] | None = None) -> list[Doc]:
    return search_scored(query, k, docs).docs


def search_scored(query: str, k: int = 2, docs: list[Doc] | None = None) -> Retrieval:
    """점수를 버리지 않는 검색 경로 — 질문 토큰 대비 커버리지 비율을 함께 돌려준다.

    커버리지 = |질문 토큰 ∩ (상위 k 문서가 커버한 토큰)| / |질문 토큰|
    절대 겹침 개수가 아니라 비율인 이유: 질문이 길수록 겹침 개수가 자연히 커진다.
    순위는 BM25로 매기지만 커버리지는 가중치 없이 센다(임계값 캘리브레이션 유지).
    """
    docs = docs if docs is not None else load_docs()
    q = set(_tokens(query))
    if not q or not docs:
        return Retrieval([], 0.0)

    tokenized = [_tokens(d.text) for d in docs]
    lengths = [len(t) for t in tokenized]
    avg_len = sum(lengths) / len(lengths)
    if not avg_len:  # 문서가 전부 비어 있으면 채점할 것이 없다
        return Retrieval([], 0.0)

    doc_sets = [set(t) for t in tokenized]
    idf = {term: _idf(term, doc_sets) for term in q}

    scored = [
        (_bm25(q, Counter(tokenized[i]), lengths[i], avg_len, idf), q & doc_sets[i], docs[i])
        for i in range(len(docs))
    ]
    # key로만 비교한다 — 점수가 같을 때 뒤 원소(set·Doc)를 비교하면 TypeError.
    scored.sort(key=lambda x: x[0], reverse=True)

    top = [(overlap, d) for score, overlap, d in scored[:k] if score > 0]
    covered: set[str] = set()
    for overlap, _ in top:
        covered |= overlap
    coverage = len(covered) / len(q)
    return Retrieval([d for _, d in top], coverage)
