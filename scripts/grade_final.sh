#!/usr/bin/env bash
# 30강 — 코스의 마지막 채점(커리큘럼 정본 4항목). 08강 6/6 · 23강 5/5 · 29강 프로브 5/5 와 같은 문법: 사람 박수가 아니라 기계의 PASS.
#   ① 측정 재현  scan_debt 를 두 번 → JSON 동일 (결정성의 기본기)
#   ② 상환 큐 안전  자동 큐의 모든 항목이 3조건 ✓✓✓ — ✗ 하나라도 끼어 있으면 FAIL
#   ③ 위반 주입  guardrails 에 `from . import llm` 을 넣어 보고 — 훅 층(exit 2) 과 파일 층(🔴 → 긴급 큐) 둘 다 막나
#   ④ 규칙 성장  ③ 을 뚫었던 변종(두 줄 importlib)을 잡는 규칙이 규칙표에 있나 (25강: 뚫리면 규칙이 자란다)
set -u
cd "$(dirname "$0")/.." || exit 2
pass=0; say() { printf '  %-26s %s\n' "$1" "$2"; }
echo "코스 마지막 채점 — 30강"
a=$(python3 scripts/scan_debt.py --json 2>/dev/null); b=$(python3 scripts/scan_debt.py --json 2>/dev/null)
if [ -n "$a" ] && [ "$a" = "$b" ]; then say "① 측정 재현(스캔 2회)" "PASS (JSON 동일)"; pass=$((pass+1)); else say "① 측정 재현(스캔 2회)" "FAIL"; fi
bad=$(awk '/^## 자동 큐/{p=1;next} /^## 사람 큐/{p=0} p' BACKLOG.md | grep '^- \[' | grep -vc '저위험✓ 가역✓ 테스트격리✓')
n=$(awk '/^## 자동 큐/{p=1;next} /^## 사람 큐/{p=0} p' BACKLOG.md | grep -c '^- \[')
if [ "$bad" -eq 0 ]; then say "② 자동 큐 3조건" "PASS (${n}건 전부 ✓✓✓)"; pass=$((pass+1)); else say "② 자동 큐 3조건" "FAIL (${bad}건 미충족)"; fi
abs="$PWD/app/guardrails.py"
printf '{"tool_name":"Edit","tool_input":{"file_path":"%s","old_string":"","new_string":"from . import llm\\n"}}' "$abs" | bash .claude/hooks/guard-architecture.sh >/dev/null 2>&1; hook=$?
tmp=$(mktemp -d); cp app/guardrails.py "$tmp/guardrails.py"; printf '\nfrom . import llm\n' >> "$tmp/guardrails.py"
python3 scripts/check_architecture.py "$tmp/guardrails.py" >/dev/null 2>&1; ci=$?; rm -rf "$tmp"
if [ "$hook" -eq 2 ] && [ "$ci" -eq 1 ]; then say "③ 위반 주입(훅·파일 두 층)" "PASS (훅 exit 2 · 파일 층 🔴 긴급 큐)"; pass=$((pass+1)); else say "③ 위반 주입(훅·파일 두 층)" "FAIL (훅 $hook · 파일 층 $ci)"; fi
tmp=$(mktemp -d); cp app/guardrails.py "$tmp/guardrails.py"; printf '\nimport importlib\n_llm = importlib.import_module("app.llm")\n' >> "$tmp/guardrails.py"
python3 scripts/check_architecture.py "$tmp/guardrails.py" >/dev/null 2>&1; var=$?; rm -rf "$tmp"
rules=$(python3 scripts/check_architecture.py --rules | grep -c '^[0-9]')
if [ "$var" -eq 1 ]; then say "④ 규칙 성장(두 줄 importlib)" "PASS (규칙 ${rules}개 — 변종도 차단)"; pass=$((pass+1)); else say "④ 규칙 성장(두 줄 importlib)" "FAIL (규칙 ${rules}개 — 변종이 통과한다 → 규칙표에 한 줄 더)"; fi
echo "PASS $pass/4"
[ "$pass" -eq 4 ]
