#!/usr/bin/env bash
# 29강 — 하네스 리뷰 루틴(6개월마다). 다섯 스텝을 한 명령으로: 같은 여섯 칸·같은 KPI·같은 프로브를 매번 쓰니
# 판정이 사람마다·그때그때 다르지 않다. 사람이 하는 건 4) 결정뿐이다.
#   1) 자가점검  harness_audit.py   2) KPI  harness_kpi.py   3) 내구성  harness_probe.sh
#   4) 결정      리포트의 '결정 필요' 항목을 사람이 갱신/폐기/수리    5) 재배포  version bump → build → /plugin update
#   bash scripts/harness_review.sh [docs/otel/console.log]   → docs/runbook/하네스_리뷰_<날짜>.md
set -u
cd "$(dirname "$0")/.." || exit 2
LOG=${1:-}; DATE=$(date +%F); OUT="docs/runbook/하네스_리뷰_${DATE}.md"
opt=(); [ -n "$LOG" ] && opt=(--otel-log "$LOG")
{
  echo "# 하네스 리뷰 — ${DATE}"; echo
  echo "> \`scripts/harness_review.sh\` 가 만든다. 같은 체크리스트·같은 KPI·같은 프로브(결정적). 사람은 4) 결정만."
  echo "> 텔레메트리 근거: ${LOG:-없음(⚪ 칸은 scripts/otel_console.py on 뒤 로그로 채운다)}"; echo
} > "$OUT"
python3 scripts/harness_audit.py "${opt[@]}" --write /tmp/_audit.md >/dev/null; audit_rc=$?; cat /tmp/_audit.md >> "$OUT"
python3 scripts/harness_kpi.py "${opt[@]}" --write "$OUT" >/dev/null
{ echo; echo "## 3) 내구성 프로브"; echo; echo '```'; } >> "$OUT"
bash scripts/harness_probe.sh >> "$OUT" 2>&1; probe_rc=$?
{ echo '```'; echo; echo "## 4) 결정 (사람)"; echo
  grep -E "⚠️|❌" /tmp/_audit.md | sed 's/^| /- [ ] /' | cut -d'|' -f1-3 || true
  [ "$probe_rc" -ne 0 ] && echo "- [ ] 죽은 게이트 수리(위 프로브 ✗)"
  echo; echo "## 5) 재배포"; echo
  echo "- 결정을 \`.claude/\` 에 반영 → \`python3 scripts/build_plugin.py\` → \`.claude-plugin/plugin.json\` version bump → push → 팀은 \`/plugin update ai-product-harness@pension_qa-team\`(28강)"
  echo "- 다음 리뷰: 6개월 뒤 같은 명령. 사람 캘린더에만 걸면 깜빡한다(19강) — 30강에서 에이전트에게 맡긴다."
} >> "$OUT"
rm -f /tmp/_audit.md
echo "→ $OUT (자가점검 exit $audit_rc · 프로브 exit $probe_rc)"
[ "$audit_rc" -eq 0 ] && [ "$probe_rc" -eq 0 ]
