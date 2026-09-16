#!/usr/bin/env bash
# 30강 — 감시자의 Bash 허용목록(debt-scanner 프론트매터 PreToolUse Bash).
#   `tools: Read, Grep, Bash` 는 쓰기 금지가 아니다 — Bash 가 있으면 `sed -i`·`>` 로 파일을 고친다(공식 sub-agents 문서).
#   07강 "Write 없음 = 역할 강제"는 유도, 보장은 이 훅이다: 감시자가 칠 수 있는 명령은 아래 목록뿐. 나머지는 exit 2.
#   목록 밖이 필요해지면 목록에 한 줄 더(규칙은 보이는 곳에).
IN=$(cat)
cmd=$(printf %s "$IN" | python3 -c 'import json,sys; print((json.load(sys.stdin).get("tool_input") or {}).get("command",""))' 2>/dev/null)
[ -n "$cmd" ] || exit 0
# 파일로 쓰는 통로는 통째로 막는다(리다이렉션·tee·sed -i·git 쓰기·인라인 파이썬)
if printf %s "$cmd" | grep -Eq '(^|[^0-9&])>|\btee\b|\bsed +-i|\brm\b|\bmv\b|\bcp\b|\bgit +(commit|push|checkout|reset|add|rebase|merge|stash)\b|python3? +-c|\bchmod\b|\btouch\b'; then
  echo "debt-scanner 는 감시자다 — 쓰기 통로 차단: $cmd (상환은 @debt-repayer 의 몫, 30강)" >&2; exit 2
fi
# 세그먼트(;·&&·|)마다 허용목록 검사
ok=1
while IFS= read -r seg; do
  seg=$(printf %s "$seg" | sed 's/^ *//;s/ *$//'); [ -z "$seg" ] && continue
  printf %s "$seg" | grep -Eq '^(bash scripts/debt_agent\.sh( --review)?|python3 scripts/(scan_debt|append_backlog|harness_audit|harness_kpi|check_architecture)\.py( .*)?|bash scripts/(harness_review|harness_probe)\.sh( .*)?|bash harness_check\.sh|(python3 -m )?pytest( .*)?|git (status|diff|log|show|branch)( .*)?|(cat|head|tail|wc|grep|ls|awk|sort|uniq|cut|tr|date|echo)( .*)?|sed -n .*)$' || ok=0
done < <(printf %s "$cmd" | sed 's/&&/\n/g; s/;/\n/g; s/|/\n/g')
[ "$ok" = 1 ] && exit 0
echo "debt-scanner 는 감시자다 — 허용목록 밖 명령: $cmd (허용: scan_debt·append_backlog·harness_*·pytest·git status/diff/log·cat/grep/…, 30강)" >&2
exit 2
