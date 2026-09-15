#!/usr/bin/env bash
# 20강 — 외부(MCP) 호출 직전 결정적 게이트. 타임아웃 정책이 환경에 없으면 차단(exit 2).
#   MCP_TIMEOUT      = 서버 연결/시작 상한(ms)   MCP_TOOL_TIMEOUT = 도구 호출 응답 상한(ms)
#   settings.json의 env에 박아두면 세션이 길어지든 compaction이 돌든 매번 만족한다(19·20강).
#   exit 2만 차단이고 stderr가 Claude에 피드백된다(14강).
missing=""
[ -n "$MCP_TIMEOUT" ] || missing="$missing MCP_TIMEOUT"
[ -n "$MCP_TOOL_TIMEOUT" ] || missing="$missing MCP_TOOL_TIMEOUT"
if [ -n "$missing" ]; then
  echo "외부 호출 차단: 타임아웃 정책 없음 —$missing. settings.json env에 상한을 고정할 것(20강 신뢰성 5요소)." >&2
  exit 2
fi
exit 0
