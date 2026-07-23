"""CLI: python -m app.main "질문" """
from __future__ import annotations

import sys

from .agent import ask


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print('사용법: python -m app.main "질문"')
        return 1
    question = " ".join(argv)
    result = ask(question)
    if result.blocked:
        prefix = "⛔ "
    elif result.low_confidence:
        prefix = "⚠️ "
    else:
        prefix = "✅ "
    print(prefix + result.answer)
    if result.sources:
        print("근거:", ", ".join(result.sources))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
