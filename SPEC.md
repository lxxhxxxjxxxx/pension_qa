# SPEC — 출력 이메일 마스킹 가드레일

## 목표
LLM 답변에 이메일이 포함되면 부분 마스킹하여 반환(차단 아님).

## 범위
- 대상: app/guardrails.py 의 출력 단계 + app/agent.py 연결
- 범위 밖: 입력 PII(이미 처리), 차단 로직 변경

## 동작
- 정규식으로 이메일 탐지 → `a***@d***.com` 형태로 마스킹
- 답변 텍스트만, sources 메타데이터는 불변

## 검증 (통과 기준)
- test: "문의는 hong@example.com 으로" → "문의는 h***@e***.com 으로"
- test: 이메일 없는 답변 → 변경 없음
- pytest -q 전체 green
