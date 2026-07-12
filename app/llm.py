"""LLM 클라이언트 — ANTHROPIC_API_KEY 있으면 호출, 없으면 stub."""
from __future__ import annotations

import os

SYSTEM = (
    "당신은 연금 안내 도우미입니다. 제공된 근거 문서 범위 안에서만 답하고, "
    "모르면 모른다고 답하세요. 세율·한도는 가상 예시임을 전제합니다."
)


def answer(question: str, contexts: list[str], model: str = "claude-haiku-4-5-20251001") -> str:
    prompt = (
        "다음 근거 문서를 참고해 질문에 답하세요.\n\n"
        + "\n\n".join(f"[근거] {c}" for c in contexts)
        + f"\n\n[질문] {question}"
    )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return f"[LLM stub] 근거 {len(contexts)}건 기반 답변 예정 — '{question}'"
    try:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model,
            max_tokens=512,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:  # 네트워크/키 오류 시 graceful fallback
        return f"[LLM 오류 fallback] {e}"
