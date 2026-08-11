"""문서 검색 — 토큰 겹침 스코어(임베딩 아님).

점수는 세 가지로 구성한다:
- **IDF 가중** — 모든 문서에 흔한 토큰(`연금`)보다 희소한 토큰(`세액공제`)을 크게 친다.
- **접두 일치** — 조사가 붙어 어긋난 토큰(`IRP로`~`IRP`, `한도가`~`한도`)에 부분 점수를 준다.
- **길이 정규화** — 문서가 길다는 이유만으로 겹침이 늘어나는 편향을 없앤다.

형태소 분석기가 아니라 여전히 휴리스틱이다(README TODO의 임베딩 검색은 그대로 남는다).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_token_re = re.compile(r"[가-힣A-Za-z0-9]+")

# 이메일 주소 덩어리(원문·마스킹본 모두). 검색어로서 의미가 없다.
_email_chunk_re = re.compile(r"\S*@\S*")

# 접두 일치 규칙 — 1글자 토큰은 아무 데나 걸려 노이즈가 되므로 제외하고,
# 접두 일치는 정확히 겹친 토큰의 절반만 인정한다.
_MIN_PARTIAL_LEN = 2
_PARTIAL_WEIGHT = 0.5


def _tokens(text: str) -> list[str]:
    # 이메일은 연금 용어가 아니므로 통째로 버린다. 특히 입력 마스킹(ADR 0001)을 거친
    # `h***@e***.com`은 `h`·`e`·`com` 같은 쓰레기 토큰으로 쪼개져 커버리지 분모만 키우고,
    # 근거 게이트(ADR 0002)를 통과할 질문을 저신뢰·보류로 끌어내린다.
    return _token_re.findall(_email_chunk_re.sub(" ", text).lower())


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


def _idf(token: str, corpus: list[set[str]]) -> float:
    """희소 토큰일수록 큰 가중치. `df=0`(문서에 없는 토큰)은 `df=1`로 스무딩한다 —
    무한대가 되면 모르는 단어 하나가 커버리지를 0으로 만들어 버린다."""
    df = sum(1 for tokens in corpus if token in tokens)
    return math.log(1 + len(corpus) / max(df, 1))


def _match_weight(token: str, doc_tokens: set[str]) -> float:
    """정확히 겹치면 1.0, 한쪽이 다른 쪽의 접두사면 부분 점수, 아니면 0.0.

    접두사로 한정하는 이유: 한국어 조사·어미는 뒤에 붙으므로(`IRP로`, `한도가`) 앞부분이 겹친다.
    접미 방향까지 열면 조사 자체(`으로`)가 복합어(`연금으로`)에 걸려 엉뚱한 문서에 점수를 준다.
    대신 복합어 안쪽 단어(`해지`~`중도해지`)는 못 잡는다 — ADR 0003의 트레이드오프.
    """
    if token in doc_tokens:
        return 1.0
    if len(token) < _MIN_PARTIAL_LEN:
        return 0.0
    for other in doc_tokens:
        if len(other) >= _MIN_PARTIAL_LEN and (token.startswith(other) or other.startswith(token)):
            return _PARTIAL_WEIGHT
    return 0.0


def search(query: str, k: int = 2, docs: list[Doc] | None = None) -> list[Doc]:
    return search_scored(query, k, docs).docs


def search_scored(query: str, k: int = 2, docs: list[Doc] | None = None) -> Retrieval:
    """점수를 버리지 않는 검색 경로 — 질문 토큰 대비 커버리지를 함께 돌려준다.

    커버리지 = Σ(상위 k 문서가 커버한 질문 토큰의 IDF) / Σ(질문 토큰 전체의 IDF)

    토큰 **개수** 비율이 아니라 IDF 가중 비율인 이유: `연금` 하나 걸린 것과
    `세액공제` 하나 걸린 것을 같은 근거로 칠 수 없다. 비율인 이유(절대 개수 아님)는
    질문이 길수록 겹침 개수가 자연히 커지기 때문(ADR 0002).
    """
    docs = docs if docs is not None else load_docs()
    q_tokens = list(dict.fromkeys(_tokens(query)))
    if not q_tokens or not docs:
        return Retrieval([], 0.0)

    corpus = [set(_tokens(d.text)) for d in docs]
    idf = {t: _idf(t, corpus) for t in q_tokens}

    scored = []
    for doc, doc_tokens in zip(docs, corpus):
        matched = {t: _match_weight(t, doc_tokens) for t in q_tokens}
        # 길이 정규화 — 긴 문서일수록 우연한 겹침이 늘어나는 편향을 상쇄한다.
        norm = math.sqrt(len(doc_tokens)) or 1.0
        scored.append((sum(idf[t] * w for t, w in matched.items()) / norm, matched, doc))

    scored.sort(key=lambda x: (-x[0], x[2].name))  # 동점은 이름순 — 순서를 결정적으로 고정
    top = [(matched, doc) for score, matched, doc in scored[:k] if score > 0]

    covered = sum(idf[t] * max((m[t] for m, _ in top), default=0.0) for t in q_tokens)
    total = sum(idf.values())
    return Retrieval([doc for _, doc in top], covered / total if total else 0.0)
