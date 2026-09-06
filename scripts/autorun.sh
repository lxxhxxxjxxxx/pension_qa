#!/usr/bin/env bash
# 21강 — 자율 실행 한 줄. 6장치를 명령 하나에 모은다.
#   ① 성공 기준  docs/autonomy/작업로그.md 의 '성공기준' 줄 — 기계(pytest)가 판정
#   ② 게이트     .claude/settings.json Stop → .claude/hooks/gate-pytest.sh (레포에 있다. 이 스크립트가 켜는 게 아니다)
#   ③ 격리       컨테이너 안에서만 --dangerously-skip-permissions. 밖이면 allowlist 로 좁혀 돈다 — 거부가 기본
#   ④ 상한       --max-turns · --max-budget-usd · MAX_THINKING_TOKENS
#   ⑤ 흔적       프롬프트가 로그 갱신·커밋을 요구하고, 게이트·렌더러가 로그에 줄을 남긴다
#   ⑥ 관측       CLAUDE_CODE_ENABLE_TELEMETRY(OTel 메트릭) · stream-json → autorun_render.py 로 턴·도구·게이트를 보이게
# 사용: scripts/autorun.sh [--dry-run] ["프롬프트"]   (추가 플래그는 AUTORUN_EXTRA="..." 로)
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=docs/autonomy/작업로그.md
MAX_TURNS=${AUTORUN_MAX_TURNS:-40}
MAX_USD=${AUTORUN_MAX_USD:-5}
export MAX_THINKING_TOKENS=${MAX_THINKING_TOKENS:-8000}
export CLAUDE_CODE_ENABLE_TELEMETRY=${CLAUDE_CODE_ENABLE_TELEMETRY:-1}

in_container() { [ -f /.dockerenv ] || grep -qsE 'docker|containerd|lxc|podman' /proc/1/cgroup; }
if in_container; then
  MODE=(--dangerously-skip-permissions)
  WHERE="컨테이너 안 — 권한 검사 생략"
else
  MODE=(--permission-mode acceptEdits
        --allowed-tools "Bash(python3 -m pytest:*)" "Bash(git add:*)" "Bash(git commit:*)"
                        "Bash(git status:*)" "Bash(git log:*)" "Bash(git diff:*)")
  WHERE="컨테이너 밖 — --dangerously-skip-permissions 거부, allowlist 로 좁혀 실행"
fi
set -f; EXTRA=(${AUTORUN_EXTRA:-}); set +f

DRY=0; [ "${1:-}" = "--dry-run" ] && { DRY=1; shift; }
PROMPT="${1:-$LOG 를 읽고 '진행' 체크리스트의 남은 항목을 이어서 하라. 성공기준은 로그의 '성공기준' 줄이 기계로 판정한다. 단계마다 로그를 갱신하고, 초록이 된 상태에서 커밋하라. 금융 판단(공제·한도·수령 안내의 결과)이 바뀌는 변경은 하지 말고 로그에 HITL 로 남겨라.}"

echo "▶ autorun: $WHERE"
echo "  상한 max-turns=$MAX_TURNS · max-budget-usd=$MAX_USD · MAX_THINKING_TOKENS=$MAX_THINKING_TOKENS"
if [ "$DRY" = 1 ]; then
  printf '  claude -p "<프롬프트>" --max-turns %s --max-budget-usd %s' "$MAX_TURNS" "$MAX_USD"; printf ' %q' "${MODE[@]}" "${EXTRA[@]}"
  echo ' --output-format stream-json --verbose | python3 scripts/autorun_render.py'
  exit 0
fi
printf -- '- [%s] ▶ autorun 시작 (%s)\n' "$(date +%H:%M:%S)" "$WHERE" >> "$LOG"
claude -p "$PROMPT" --max-turns "$MAX_TURNS" --max-budget-usd "$MAX_USD" "${MODE[@]}" "${EXTRA[@]}" \
  --output-format stream-json --verbose < /dev/null | python3 scripts/autorun_render.py
