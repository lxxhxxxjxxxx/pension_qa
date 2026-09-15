#!/usr/bin/env bash
# 29강 — 내구성 프로브. 게이트로 코드를 테스트하지만, 게이트 자체는 누가 테스트하나.
#   일부러 나쁜 것을 넣고 게이트가 아직 막는지 본다(16강 "버그 PR 주입"을 정기 루틴으로). 막으면 생존, 통과시키면
#   조용히 죽은 게이트다 — 사고가 나기 전엔 아무도 모른다. 다섯 프로브 전부 되돌린다(trap).
#   조건: 워킹트리가 깨끗해야 한다(되돌리기가 git checkout 이라서). 결과: "게이트 생존 N/5", 하나라도 죽으면 exit 1.
set -u
cd "$(dirname "$0")/.." || exit 2
if [ -n "$(git status --porcelain -- app tests docs/autonomy)" ]; then
  echo "워킹트리가 깨끗하지 않다(app·tests·docs/autonomy) — 커밋하거나 stash 한 뒤 다시." >&2; exit 2
fi
restore() {
  git checkout -q -- app/pension_calc.py app/agent.py docs/autonomy/작업로그.md 2>/dev/null
  rm -f tests/test__probe_fail.py; rm -rf .claude/.gate/probe
}
trap restore EXIT
alive=0; total=5
say() { printf '  %-34s %s\n' "$1" "$2"; }
echo "내구성 프로브 — 나쁜 것을 넣고 게이트가 막나 (전부 되돌림)"

# P1 금액 경로에 float — 08강 harness_check ⑥ · 13강 스킬 grep 게이트
before=$(bash harness_check.sh); printf '\n\ndef _probe(x):\n    return float(x) * 1.1\n' >> app/pension_calc.py
after=$(bash harness_check.sh); gate=$(grep -n "float(" app/pension_calc.py app/agent.py || echo "OK")
if [ "$after" != "$before" ] && [ "$gate" != "OK" ]; then say "P1 float in pension_calc" "생존 ✓ ($before → $after · 스킬 grep 적중)"; alive=$((alive+1)); else say "P1 float in pension_calc" "죽음 ✗ ($before → $after)"; fi
git checkout -q -- app/pension_calc.py

# P2 주민번호가 답변에 — 03·11강 출력 유출 가드레일(check_output_leak)
r=$(python3 -c 'from app.guardrails import check_output_leak as c; print("BLOCK" if not c("고객 주민번호는 901010-1234567 입니다").ok else "PASS")')
if [ "$r" = "BLOCK" ]; then say "P2 주민번호 in answer" "생존 ✓ (check_output_leak 차단)"; alive=$((alive+1)); else say "P2 주민번호 in answer" "죽음 ✗ (유출 통과)"; fi

# P3 bare except — 13강 스킬 grep 게이트
printf '\n\ntry:\n    pass\nexcept:\n    pass\n' >> app/agent.py
r=$(grep -rEn "except\s*:" app/ || echo "OK")
if [ "$r" != "OK" ]; then say "P3 bare except in agent" "생존 ✓ (스킬 grep 적중)"; alive=$((alive+1)); else say "P3 bare except in agent" "죽음 ✗"; fi
git checkout -q -- app/agent.py

# P4 빨간 테스트 — 14·21강 Stop 게이트(gate-pytest.sh, exit 2)
printf 'def test__probe():\n    assert False, "probe"\n' > tests/test__probe_fail.py
echo '{"session_id":"probe","stop_hook_active":false}' | GATE_MAX_BLOCKS=99 bash .claude/hooks/gate-pytest.sh >/dev/null 2>&1; rc=$?
rm -f tests/test__probe_fail.py; git checkout -q -- docs/autonomy/작업로그.md 2>/dev/null; rm -rf .claude/.gate/probe
if [ "$rc" -eq 2 ]; then say "P4 failing test → Stop" "생존 ✓ (gate-pytest exit 2)"; alive=$((alive+1)); else say "P4 failing test → Stop" "죽음 ✗ (exit $rc)"; fi

# P5 와이드 변경 — 25강 surgical 상한(guard-diff-size.sh, exit 2)
printf '\n# probe\n' >> app/pension_calc.py
GUARD_MAX_FILES=0 bash .claude/hooks/guard-diff-size.sh >/dev/null 2>&1; rc=$?
git checkout -q -- app/pension_calc.py
if [ "$rc" -eq 2 ]; then say "P5 wide diff → PreToolUse" "생존 ✓ (guard-diff-size exit 2)"; alive=$((alive+1)); else say "P5 wide diff → PreToolUse" "죽음 ✗ (exit $rc)"; fi

echo "게이트 생존 $alive/$total"
[ "$alive" -eq "$total" ]
