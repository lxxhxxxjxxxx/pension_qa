"""문서 검색 — BM25 계열 토큰 스코어(임베딩 아님).

점수는 "질문 토큰이 몇 개 겹쳤나"가 아니라 "얼마나 변별력 있는 토큰이 겹쳤나"로 매긴다.
겹침 개수만 세면 다음이 전부 같은 1점이었다:

- 모든 문서에 나오는 토큰(`연금`·`가상`·`예시`·`문서`)과 한 문서에만 있는 토큰(`IRP`·`세액공제`)
- 그 토큰을 한 번 언급한 문서와 본문 내내 다루는 문서
- 짧은 문서와, 길어서 우연히 겹칠 확률이 높은 문서

그래서 IDF(희소성) · TF 포화 · 길이 정규화 세 가지를 넣었다.

⚠️ 바뀐 것은 **랭킹 점수**뿐이고 `Retrieval.coverage`(ADR 0002 게이트의 입력)의 정의는
"질문 토큰 중 상위 k 문서가 커버한 비율" 그대로다. 커버리지 정의를 손대면
`guardrails.HARD_THRESHOLD`/`SOFT_THRESHOLD`가 곧바로 재캘리브레이션 대상이 된다
(조사 정규화·임베딩 도입이 여기에 해당 — 아직 안 함).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# BM25 표준값. k1=TF 포화 속도, b=길이 정규화 강도.
K1 = 1.5
B = 0.75

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


@dataclass
class ScoredDoc:
    """랭킹용 중간 표현 — 점수는 밖으로 노출하지 않는다(ADR 0002)."""

    doc: Doc
    score: float
    overlap: set[str]


def _idf(df: int, total: int) -> float:
    """희소한 토큰일수록 큰 가중치. 모든 문서에 있는 토큰도 0이 아니라 0에 가까운 값이다.

    0으로 떨어뜨리면 흔한 토큰만 겹친 문서가 검색 결과에서 통째로 사라져
    "근거 문서를 찾지 못함"(빈 결과) 경로의 동작이 조용히 바뀐다 — 그건 별도 결정 사항.
    """
    return math.log(1 + (total - df + 0.5) / (df + 0.5))


def score_docs(query: str, docs: list[Doc]) -> list[ScoredDoc]:
    """질문 대비 BM25 점수로 문서를 내림차순 정렬한다(동점이면 이름순 — 결과 재현성)."""
    q = set(_tokens(query))
    if not docs or not q:
        return []

    doc_counts = [Counter(_tokens(d.text)) for d in docs]
    lengths = [sum(c.values()) for c in doc_counts]
    avg_len = sum(lengths) / len(docs)

    idf = {t: _idf(sum(1 for c in doc_counts if t in c), len(docs)) for t in q}

    scored = []
    for doc, counts, length in zip(docs, doc_counts, lengths):
        overlap = {t for t in q if t in counts}
        norm = 1 - B + B * (length / avg_len if avg_len else 1)
        score = sum(
            idf[t] * (counts[t] * (K1 + 1)) / (counts[t] + K1 * norm) for t in overlap
        )
        scored.append(ScoredDoc(doc, score, overlap))

    scored.sort(key=lambda s: (-s.score, s.doc.name))
    return scored


def search(query: str, k: int = 2, docs: list[Doc] | None = None) -> list[Doc]:
    return search_scored(query, k, docs).docs


def search_scored(query: str, k: int = 2, docs: list[Doc] | None = None) -> Retrieval:
    """점수를 버리지 않는 검색 경로 — 질문 토큰 대비 커버리지 비율을 함께 돌려준다.

    커버리지 = |질문 토큰 ∩ (상위 k 문서가 커버한 토큰)| / |질문 토큰|
    절대 겹침 개수가 아니라 비율인 이유: 질문이 길수록 겹침 개수가 자연히 커진다.
    """
    docs = docs if docs is not None else load_docs()
    q = set(_tokens(query))

    top = [s for s in score_docs(query, docs)[:k] if s.score > 0]
    covered: set[str] = set()
    for s in top:
        covered |= s.overlap
    coverage = len(covered) / len(q) if q else 0.0
    return Retrieval([s.doc for s in top], coverage)
