---
paths: ["app/guardrails.py"]
---
# 가드레일 규칙
- 입력(PII·범위)·출력(유출) 양쪽 고려, fail-closed(애매하면 차단)
- 차단 시 이유 문자열 반환(Check(False, reason))
