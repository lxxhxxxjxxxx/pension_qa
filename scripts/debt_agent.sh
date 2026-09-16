#!/usr/bin/env bash
# 30강 — 부채 에이전트의 결정적 몸통: 스캔 → 백로그 갱신 → 우선순위 → 요약. 27강 도구를 **사람 손 없이** 돌리는 것이 30강의 차이다.
#   방아쇠 둘: 이벤트(SessionStart 훅 .claude/hooks/debt-agent-session.sh) · 주기(.claude/loop.md / docs/ci/debt-agent.yml → @debt-scanner).
#   --review 를 주면 29강 루틴(harness_review.sh — 자가점검·KPI·프로브)까지 같은 자리에서 돈다(29강이 약속한 "에이전트에게 맡긴다").
#   --quiet 는 SessionStart 용(요약 3줄만). 흔적은 .claude/debt_agent.log(gitignore) — 워킹트리를 더럽히지 않는다(29강 프로브 조건).
set -u
cd "$(dirname "$0")/.." || exit 2
QUIET=0; REVIEW=0
for a in "$@"; do case "$a" in --quiet) QUIET=1;; --review) REVIEW=1;; esac; done
scan=$(python3 scripts/scan_debt.py --to-backlog 2>/dev/null)
[ "$QUIET" = 0 ] && printf '%s\n\n' "$scan"
count() { awk -v s="$1" -v e="$2" '$0 ~ "^## "s {p=1; next} $0 ~ "^## "e {p=0} p' BACKLOG.md | grep -c '^- \[ \]'; }
auto=$(count "자동 큐" "사람 큐"); human=$(count "사람 큐" "지표"); metric=$(awk '/^## 지표/{p=1;next} p' BACKLOG.md | grep -c '^- \[ \]')
next=$(awk '/^## 자동 큐/{p=1;next} /^## 사람 큐/{p=0} p' BACKLOG.md | grep -m1 '^- \[ \]' | sed 's/^- \[ \] //')
echo "부채 에이전트 $(date +%F) — 자동 상환 후보 ${auto}건 · 사람 큐 ${human}건 · 지표 ${metric}건 (BACKLOG.md)"
if [ -n "$next" ]; then echo "다음 상환 대상(자동 큐 첫 줄): $next"; echo "→ @debt-repayer 에게 이 한 항목을 맡긴다 · 검문 scripts/repay_gate.sh · 기록 scripts/record_repayment_adr.py"; else echo "자동 큐 비어 있음 — 상환할 것 없음"; fi
mkdir -p .claude; echo "- [$(date +%F' '%H:%M:%S)] debt_agent — 자동 $auto · 사람 $human · 지표 $metric" >> .claude/debt_agent.log
[ "$REVIEW" = 1 ] && { echo; bash scripts/harness_review.sh; }
exit 0
