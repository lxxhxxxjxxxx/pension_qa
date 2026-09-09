p=0
grep -q "sources" CLAUDE.md                               && p=$((p+1))  # ① 컨벤션 명시
grep -q "paths:" .claude/rules/guardrails.md              && p=$((p+1))  # ② path-scoped rules
grep -q '"deny"' .claude/settings.json                    && p=$((p+1))  # ③ 강제 게이트
c=1; for r in explorer implementer reviewer verifier; do [ -f ".claude/agents/$r.md" ] || c=0; done
[ "$c" -eq 1 ]                                            && p=$((p+1))  # ④ 핵심 4역할 존재(26강: 리뷰어는 렌즈별 다중화 → '정확히 4개'가 아니라 '4역할 존재')
ls docs/adr/0001-* >/dev/null 2>&1                        && p=$((p+1))  # ⑤ 결정 기록
! grep -q "float(" app/pension_calc.py                    && p=$((p+1))  # ⑥ 금지 토큰 부재
echo "PASS $p/6"
