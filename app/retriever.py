"""문서 검색 — BM25 랭킹(임베딩 아님).

기존 구현은 "질문 토큰 중 문서에 등장하는 종류 수"를 셌기 때문에
(1) 흔한 토큰('연금')과 변별력 있는 토큰('IRP')을 똑같이 세고
(2) 긴 문서가 우연히 겹칠 확률이 높아 유리하고
(3) 점수가 문서 간 비교용 정수라 임계값을 잡을 수 없었다.

BM25 는 셋 다 다룬다: IDF 로 흔한 토큰을 깎고, 문서 길이로 정규화하며,
term frequency 를 포화시켜 한 단어 반복이 순위를 지배하지 못하게 한다.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

K1 = 1.5              # term frequency 포화 계수
B = 0.75              # 문서 길이 정규화 강도
TITLE_BOOST = 2.0     # 파일명(제목)에 있는 토큰 가중
MIN_SCORE = 0.05      # 이 아래는 '근거 없음'으로 본다
RELATIVE_CUTOFF = 0.25  # 1위 대비 이 비율 미만이면 곁가지로 보고 버린다

_token_re = re.compile(r"[가-힣A-Za-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _token_re.findall(text.lower())


@dataclass(frozen=True)
class Doc:
    name: str
    text: str


@dataclass(frozen=True)
class Hit:
    doc: Doc
    score: float


@dataclass(frozen=True)
class Index:
    """BM25 통계 — 질의마다 다시 계산하지 않도록 미리 뽑아둔다."""

    docs: tuple[Doc, ...]
    tfs: tuple[Counter, ...]
    title_tokens: tuple[frozenset[str], ...]
    lengths: tuple[int, ...]
    avg_len: float
    idf: dict[str, float]


def load_docs(data_dir: Path = DATA_DIR) -> list[Doc]:
    return [Doc(p.stem, p.read_text(encoding="utf-8")) for p in sorted(data_dir.glob("*.md"))]


def build_index(docs: Sequence[Doc]) -> Index:
    tfs = [Counter(_tokens(d.text)) for d in docs]
    lengths = [sum(tf.values()) for tf in tfs]
    n = len(docs)

    df: Counter = Counter()
    for tf in tfs:
        df.update(tf.keys())

    # +1 형태의 IDF — 모든 문서에 등장하는 토큰도 음수가 되지 않고 0 에 수렴한다.
    idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    return Index(
        docs=tuple(docs),
        tfs=tuple(tfs),
        title_tokens=tuple(frozenset(_tokens(d.name)) for d in docs),
        lengths=tuple(lengths),
        avg_len=(sum(lengths) / n) if n else 0.0,
        idf=idf,
    )


_cached_index: Index | None = None


def default_index() -> Index:
    """`data/` 기본 인덱스(프로세스 내 1회만 빌드)."""
    global _cached_index
    if _cached_index is None:
        _cached_index = build_index(load_docs())
    return _cached_index


def clear_cache() -> None:
    global _cached_index
    _cached_index = None


def _score(index: Index, i: int, query_terms: Sequence[str]) -> float:
    tf = index.tfs[i]
    norm = K1 * (1 - B + B * (index.lengths[i] / index.avg_len))
    total = 0.0
    for term in query_terms:
        freq = tf.get(term, 0)
        if not freq:
            continue
        weight = index.idf.get(term, 0.0)
        if term in index.title_tokens[i]:
            weight *= TITLE_BOOST
        total += weight * (freq * (K1 + 1)) / (freq + norm)
    return total


def search_scored(
    query: str,
    k: int = 2,
    docs: Sequence[Doc] | None = None,
    min_score: float = MIN_SCORE,
) -> list[Hit]:
    """상위 k개를 (문서, 점수)로 반환. `min_score` 미만은 버린다."""
    index = default_index() if docs is None else build_index(docs)
    if not index.docs or not index.avg_len:
        return []

    # 중복 토큰은 한 번만 — 질문에서 같은 단어를 반복해도 점수가 부풀지 않게.
    query_terms = list(dict.fromkeys(_tokens(query)))
    if not query_terms:
        return []

    hits = [Hit(doc, _score(index, i, query_terms)) for i, doc in enumerate(index.docs)]
    hits = [h for h in hits if h.score >= min_score]
    if not hits:
        return []

    # 동점일 때 순서가 흔들리지 않도록 이름을 2차 키로.
    hits.sort(key=lambda h: (-h.score, h.doc.name))
    # 1위와 격차가 큰 문서는 k 를 채우려고 억지로 끌고 오지 않는다.
    floor = hits[0].score * RELATIVE_CUTOFF
    return [h for h in hits[:k] if h.score >= floor]


def search(
    query: str,
    k: int = 2,
    docs: Sequence[Doc] | None = None,
    min_score: float = MIN_SCORE,
) -> list[Doc]:
    """점수가 필요 없을 때 쓰는 얇은 래퍼."""
    return [h.doc for h in search_scored(query, k=k, docs=docs, min_score=min_score)]
