#!/usr/bin/env bash
# 30강 — 아키텍처 가드(PreToolUse Edit|Write). 들어올 편집 내용을 scripts/check_architecture.py 규칙표로 검사, 위반이면 exit 2.
#   왜 PreToolUse 인가: PostToolUse 는 편집이 파일에 닿은 뒤라 exit 2 가 못 막는다(stderr 만 Claude 에게) — 공식 hooks 문서.
#   왜 python3 인가: 촬영 PC·팀원 PC 에 jq 가 없을 수 있다(2026-09-15 실측 — 파이프가 죽으면 `|| exit 0` 이 삼켜 '조용히 안 막는' 훅이 된다).
#   file_path 는 절대 경로로 온다 — 스크립트가 basename 으로 본다(상대 경로 비교는 영원히 거짓).
#   플러그인으로 배포되면 스크립트가 옆에 없을 수 있다 → 레포의 scripts/ 를 먼저, 없으면 훅 옆 사본.
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || true
if [ -f scripts/check_architecture.py ]; then exec python3 scripts/check_architecture.py --hook; fi
here="$(cd "$(dirname "$0")" && pwd)"
[ -f "$here/check_architecture.py" ] && exec python3 "$here/check_architecture.py" --hook
exit 0
