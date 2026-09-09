#!/usr/bin/env bash
# ConfigChange 감사 훅 (24강 운영·blameless 감사)
# ConfigChange 이벤트: 세션 중 설정 파일이 바뀌면 발화한다.
#   matcher = 설정 source(user_settings·project_settings·local_settings·policy_settings·skills)
#   변경을 차단할 수도 있다(policy_settings 제외) — 여기선 '감사'라 로깅 후 통과(exit 0).
#   특정 source 변경을 막고 싶으면 그 자리에서 exit 2 하면 된다.
# 왜: 운영에서 "누가 언제 어떤 설정을 바꿨나"가 장애 원인 추적의 첫 단서다(ADR 0009 가설 파이프라인).
set -euo pipefail

log="${CONFIG_AUDIT_LOG:-${CLAUDE_PROJECT_DIR:-.}/.claude/config_audit.log}"

src="$(cat | python3 -c "import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
print(d.get('source') or d.get('config_source') or 'unknown')" 2>/dev/null || printf 'unknown')"

printf '%s\tConfigChange\tsource=%s\n' "$(date -u +%FT%TZ)" "$src" >> "$log"
exit 0
