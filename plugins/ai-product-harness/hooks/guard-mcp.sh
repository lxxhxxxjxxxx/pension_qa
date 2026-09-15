#!/usr/bin/env bash
# 22강 — MCP 호출 직전 게이트. 쓰기성 도구(write/create/update/delete/put/post)를 exit 2로 차단.
#   pension_qa MCP는 읽기 전용 계약 — 서버가 write_doc 을 내밀어도(스코프 불일치) 호출을 못 나가게 막는다.
#   PreToolUse 입력 JSON의 tool_name(mcp__<server>__<tool>)을 본다. exit 2만 차단, stderr가 Claude에 피드백(14강).
#   20강 guard-external.sh(타임아웃 정책 검사)와 같은 mcp__.* matcher에 함께 걸린다 — 20강 게이트는 그대로.
input=$(cat)
tool=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_name",""))' 2>/dev/null)
case "$tool" in
  mcp__*__*write*|mcp__*__*create*|mcp__*__*update*|mcp__*__*delete*|mcp__*__*put*|mcp__*__*post*)
    echo "MCP 차단: '$tool' 은 쓰기성 도구 — pension_qa MCP는 읽기 전용 계약(18강 스코프)." >&2
    exit 2 ;;
esac
exit 0
