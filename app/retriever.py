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


def search(query: str, k: int = 2, docs: list[Doc] | None = None) -> list[Doc]:
    docs = docs if docs is not None else load_docs()
    q = set(_tokens(query))
    scored = []
    for d in docs:
        overlap = len(q & set(_tokens(d.text)))
        scored.append((overlap, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for score, d in scored[:k] if score > 0]
