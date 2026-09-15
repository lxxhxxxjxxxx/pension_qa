#!/usr/bin/env bash
# 21강 — Stop 게이트. 14강의 "테스트 초록까지 멈춤을 막는다"에 두 가지를 얹었다.
#   상한: 같은 세션에서 GATE_MAX_BLOCKS(기본 3)번 연속 막히면 더 안 막고 사람에게 넘긴다(장치 4·6 — HITL)
#   흔적: 막힐 때·넘길 때 docs/autonomy/작업로그.md 에 한 줄 남긴다(장치 5)
#   입력 JSON의 stop_hook_active=true 는 "게이트가 한 번 막아서 돌아온 턴"이라는 표시(14강).
#   exit 2 만 차단이고 그때 stderr 가 Claude 에 피드백된다. exit 0 은 멈춤 허용.
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
input=$(cat)
session=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("session_id","nosession"))' 2>/dev/null || echo nosession)
active=$(printf '%s' "$input" | python3 -c 'import json,sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())' 2>/dev/null || echo false)
MAX=${GATE_MAX_BLOCKS:-3}
LOG=docs/autonomy/작업로그.md
state=".claude/.gate/$session"; mkdir -p .claude/.gate
stamp() { date +%H:%M:%S; }

if out=$(python3 -m pytest -q 2>&1); then
  rm -f "$state"
  exit 0                                   # 초록 → 멈춰도 된다(루프가 스스로 끝난다)
fi

n=0; [ -f "$state" ] && n=$(cat "$state"); n=$((n+1)); echo "$n" > "$state"

if [ "$n" -ge "$MAX" ]; then                # 상한 → 더 안 막는다. 사람에게 넘긴다.
  msg="게이트 ${n}회 연속 미통과 — 자율 중단, 사람 확인 필요(HITL)"
  [ -f "$LOG" ] && printf -- '- [%s] ⛔ %s\n' "$(stamp)" "$msg" >> "$LOG"
  printf '{"systemMessage": "%s"}\n' "$msg"
  exit 0
fi

[ -f "$LOG" ] && printf -- '- [%s] 게이트 차단 %d/%d (stop_hook_active=%s)\n' "$(stamp)" "$n" "$MAX" "$active" >> "$LOG"
printf '%s\n' "$out" | tail -n 5 >&2
echo "테스트 미통과 (${n}/${MAX}) — 실패 케이스를 고치고 계속. 고칠 수 없으면 $LOG 에 이유를 적어라." >&2
exit 2
