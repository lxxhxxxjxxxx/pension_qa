#!/usr/bin/env bash
# 25강 — surgical 상한 게이트. surgical 규칙(체크리스트)은 유도, 유도는 보장이 아니다(05강) → 상한은 기계로.
#   변경 파일 수 / 추가·삭제 라인 수가 상한을 넘으면 exit 2로 정지(리뷰 불가능한 와이드 변경 차단, 21강 표류 감독).
#   상한: GUARD_MAX_FILES(기본 5) · GUARD_MAX_LINES(기본 300). 기본은 워킹트리 diff, 인자 있으면 그 범위.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
MAXF=${GUARD_MAX_FILES:-5}; MAXL=${GUARD_MAX_LINES:-300}
stat=$(git diff --numstat "$@" 2>/dev/null)
files=$(printf '%s\n' "$stat" | grep -c . )
lines=$(printf '%s\n' "$stat" | awk '{a+=$1; d+=$2} END{print a+d+0}')
if [ "$files" -gt "$MAXF" ] || [ "$lines" -gt "$MAXL" ]; then
  echo "surgical 상한 초과: 파일 ${files}(>${MAXF}) · 라인 ${lines}(>${MAXL}) — 변경이 너무 넓어 리뷰 불가. 요청 범위로 좁힐 것(25강)." >&2
  exit 2
fi
exit 0
