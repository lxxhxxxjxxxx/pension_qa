#!/usr/bin/env bash
# 30강 — 상환 검문(기계 층). @debt-repayer 가 만든 커밋 하나가 '그 항목만 갚았나'를 결정적으로 본다.
#   bash scripts/repay_gate.sh app/agent.py:34 [base]     검문 대상 = 가장 최근 `repay(` 커밋 하나(base 기본 그 직전). ADR 커밋이 위에 있어도 같은 답
#   ① 변경 파일이 정확히 그 파일 하나  ② surgical 상한(25강 guard-diff-size, 파일 1·라인 60)  ③ 아키텍처 검사(30강)  ④ 테스트 초록
#   ⑤ 그 항목이 BACKLOG 자동 큐에 있다(3조건 ✓✓✓) — 사람 큐 항목을 에이전트가 갚았으면 FAIL
#   확률적 검문(25·26강 리뷰어 /code-review)은 이 위에 한 층 더 — 이 스크립트는 리뷰어를 대신하지 않고, 리뷰어가 못 하는 '기계 확인'만 한다.
set -u
cd "$(dirname "$0")/.." || exit 2
item=${1:-}
[ -n "$item" ] || { echo "사용법: repay_gate.sh <file:line> [base]" >&2; exit 2; }
# 상환 커밋 = 메시지가 `repay(` 로 시작하는 가장 최근 커밋(없으면 HEAD). ADR 커밋이 그 위에 얹혀도 검문 대상은 상환 커밋 하나다(라이브 실측에서 잡은 함정).
head=$(git log -n 50 --format=%H --grep='^repay(' | head -1); head=${head:-HEAD}
base=${2:-$head~1}
file=${item%%:*}; pass=0; total=5
say() { printf '  %-30s %s\n' "$1" "$2"; }
echo "상환 검문 — $item (상환 커밋 $(git rev-parse --short "$head") · base $(git rev-parse --short "$base"))"
changed=$(git diff --name-only "$base" "$head")
if [ "$changed" = "$file" ]; then say "① 파일 하나·그 파일" "PASS"; pass=$((pass+1)); else say "① 파일 하나·그 파일" "FAIL ($(printf %s "$changed" | tr '\n' ' '))"; fi
if GUARD_MAX_FILES=1 GUARD_MAX_LINES=60 bash .claude/hooks/guard-diff-size.sh "$base" "$head" >/dev/null 2>&1; then say "② surgical 상한(1파일·60줄)" "PASS"; pass=$((pass+1)); else say "② surgical 상한(1파일·60줄)" "FAIL"; fi
if python3 scripts/check_architecture.py "$file" >/dev/null 2>&1; then say "③ 아키텍처 규칙" "PASS"; pass=$((pass+1)); else say "③ 아키텍처 규칙" "FAIL"; fi
if out=$(python3 -m pytest -q 2>&1); then say "④ 테스트" "PASS ($(printf %s "$out" | tail -1))"; pass=$((pass+1)); else say "④ 테스트" "FAIL"; fi
if awk '/^## 자동 큐/{p=1;next} /^## 사람 큐/{p=0} p' BACKLOG.md | grep -q -- "$item"; then say "⑤ 자동 큐 항목(3조건 ✓✓✓)" "PASS"; pass=$((pass+1)); else say "⑤ 자동 큐 항목(3조건 ✓✓✓)" "FAIL (자동 큐에 없음 — 사람 큐는 에이전트 몫이 아니다)"; fi
echo "검문 $pass/$total$([ "$pass" -eq "$total" ] && echo ' → 머지 가능 · scripts/record_repayment_adr.py 로 기록' || echo ' → 머지 불가 · 사람 확인')"
[ "$pass" -eq "$total" ]
