"""문서 검색 — IDF 가중 토큰 겹침 스코어(임베딩 아님).

한 번의 채점이 두 곳에 쓰인다.

- **랭킹** — 상위 k개 문서를 고른다.
- **커버리지** — 근거 부실 게이트(ADR 0002·0003)의 입력.

둘은 반드시 같은 가중치를 써야 한다. 검색이 근거로 친 토큰과 게이트가 채점하는
토큰이 어긋나면 "검색은 찾았는데 게이트는 못 찾았다"는 모순이 생긴다.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_token_re = re.compile(r"[가-힣A-Za-z0-9]+")

# 토큰 정규식이 한글·영숫자를 한 덩어리로 잡아 `한도가`·`irp로`·`해지하면`이 통째로 한 토큰이 된다.
# 형태소 분석기 없이 아래 조사·어미를 잘라낸 형태를 후보로 함께 들고 다니며,
# 질문과 문서 양쪽을 같은 방식으로 편다. 길이 내림차순 — `에서는`을 `는`보다 먼저 떼야 한다.
_SUFFIXES = (
    "에서는", "으로는", "에게는", "까지는", "부터는",
    "하나요", "되나요", "인가요", "합니다", "됩니다", "입니다", "이라면",
    "에서", "으로", "에게", "한테", "까지", "부터", "보다", "처럼", "만큼",
    "이나", "라도", "이란", "밖에", "조차", "마저",
    "하면", "하는", "하고", "하며", "해서", "하여", "한다", "되면",
    "은", "는", "이", "가", "을", "를", "의", "에", "와", "과", "도", "만", "로", "랑",
)

# 접사를 뗀 뒤 남아야 하는 최소 길이. `한도`에서 `도`를 떼어 `한`으로 만드는 사고를 막고,
# 한 글자 토큰이 아무 복합어에나 걸리는 것도 함께 막는다.
_MIN_STEM_LEN = 2

# 홀로 떨어져 나온 접사는 내용어가 아니다. 질의에서 빼지 않으면 `"... 문의는 ... 으로"`의
# `으로`가 문서의 `연금으로` 안에 걸려 근거로 잡히고, 랭킹까지 뒤집는다.
_SUFFIX_SET = frozenset(_SUFFIXES)


def _tokens(text: str) -> list[str]:
    return _token_re.findall(text.lower())


def _strip_suffix(token: str) -> str | None:
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM_LEN:
            return token[: -len(suffix)]
    return None


def _variants(token: str) -> set[str]:
    """토큰 + 조사·어미를 뗀 형태들. `가입일로부터` → {가입일로부터, 가입일로, 가입일}."""
    forms = {token}
    stem = _strip_suffix(token)
    while stem and stem not in forms:
        forms.add(stem)
        stem = _strip_suffix(stem)
    return forms


def _hits(q_forms: set[str], doc_forms: set[str]) -> bool:
    """질문 토큰이 문서에 근거를 갖는가.

    정확히 겹치거나, 질문 쪽 형태가 문서 토큰 **안에** 들어 있으면 근거로 친다
    (`해지` ⊂ `중도해지`, `과세` ⊂ `종합과세`). 한국어 복합명사를 형태소 분석 없이
    잇기 위한 장치다. 포함 방향은 질문 → 문서 한쪽만 허용한다. 반대로 열면
    문서의 `연금`이 질문의 `연금소득세`를 커버한 것으로 쳐서 특이 용어의 IDF가 무너진다.
    """
    if q_forms & doc_forms:
        return True
    return any(
        len(form) >= _MIN_STEM_LEN and any(form in d for d in doc_forms) for form in q_forms
    )


def _idf(df: int, n_docs: int) -> float:
    """BM25 계열 스무딩 IDF.

    모든 문서에 있는 흔한 토큰(`연금`)은 0에 가깝고 특정 문서에만 있는 토큰
    (`세액공제`)이 무겁다. `df`는 1로 하한을 둔다 — 어느 문서에도 없는 토큰
    (`hong`, `점심`)이 **가장 희귀한 실제 용어보다 더 무거워지면** 질문에 이메일 한 줄만
    붙어도 커버리지가 무너지기 때문. 미지의 토큰은 "가장 희귀한 용어만큼"까지만 친다.
    """
    return math.log(1 + (n_docs - max(df, 1) + 0.5) / (max(df, 1) + 0.5))


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


def _doc_forms(doc: Doc) -> set[str]:
    forms: set[str] = set()
    for token in _tokens(doc.text):
        forms |= _variants(token)
    return forms


def search(query: str, k: int = 2, docs: list[Doc] | None = None) -> list[Doc]:
    return search_scored(query, k, docs).docs


def search_scored(query: str, k: int = 2, docs: list[Doc] | None = None) -> Retrieval:
    """점수를 버리지 않는 검색 경로 — 질문 토큰 대비 커버리지를 함께 돌려준다.

    커버리지 = Σ idf(상위 k 문서가 커버한 질문 토큰) / max(Σ idf(질문 토큰), 최소 질의 정보량)

    겹침 **개수**가 아니라 비율인 이유: 질문이 길수록 겹침 개수가 자연히 커진다.
    개수 비율이 아니라 **IDF 가중** 비율인 이유: 모든 토큰을 같은 무게로 세면
    흔한 토큰 하나만 겹쳐도 근거를 찾은 것처럼 보인다.
    분모에 **하한**을 두는 이유: 순수 비율이면 `"연금"` 한 단어 질문이 커버리지 1.00으로
    게이트를 그냥 통과한다(ADR 0002가 남긴 구조적 구멍). 하한은 "가장 희귀한 용어 하나만큼의
    정보량"이라, 그만큼도 안 되는 질문은 만점을 받지 못한다(ADR 0003).
    """
    docs = docs if docs is not None else load_docs()
    q_tokens = {t for t in _tokens(query) if t not in _SUFFIX_SET}
    if not q_tokens or not docs:
        return Retrieval([], 0.0)

    q_variants = {t: _variants(t) for t in q_tokens}
    covered_per_doc = [
        ({t for t, forms in q_variants.items() if _hits(forms, doc_forms)}, doc)
        for doc, doc_forms in ((d, _doc_forms(d)) for d in docs)
    ]

    weight = {
        t: _idf(sum(1 for covered, _ in covered_per_doc if t in covered), len(docs))
        for t in q_tokens
    }

    def mass(tokens: set[str]) -> float:
        return sum(weight[t] for t in tokens)

    ranked = sorted(covered_per_doc, key=lambda pair: mass(pair[0]), reverse=True)
    top = [(covered, d) for covered, d in ranked if covered][:k]

    hit: set[str] = set()
    for covered, _ in top:
        hit |= covered

    denominator = max(mass(q_tokens), _idf(1, len(docs)))
    return Retrieval([d for _, d in top], mass(hit) / denominator)
