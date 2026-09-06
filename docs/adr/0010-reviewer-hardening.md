# ADR 0010 — 리뷰어 견고화 + 변경 범위 제어 (25강)

- 날짜: 2026-09-06 · 상태: 채택
- 07강(리뷰어 서브에이전트)·13강(code-review 스킬)의 리뷰어를 **운영에서 믿을 수 있게** 세운다. 24강 안티패턴 ④(피드백 루프 부재)의 처방.

## 결정 1 — 리뷰어 견고화 5요소
1. **명확한 리뷰 스펙**: `.claude/skills/code-review/checklist.md`(심각도 🔴 Important/🟡 Nit/🟣 Pre-existing·검증 바 file:line·nit 상한 5). REVIEW.md는 GitHub 매니지드 전용이라 로컬 스킬은 안 읽음 — 스펙은 checklist.md.
2. **output-style로 출력 포맷 표준화**: `.claude/output-styles/reviewer.md`(`keep-coding-instructions: false`). 매번 같은 구조 → severity 파싱해 결정적 게이트(매니지드 code-review조차 check run이 neutral·로컬 출력은 텍스트라 게이트는 우리가 건다). = **결정적 후처리**.
3. **컨텍스트 격리**: reviewer 서브에이전트(독립 컨텍스트 창·`tools`에 Write 없음, 07강) 또는 `--fork-session`. 자기 bias·오염·과신 차단.
4. **결정적 게이트 결합**: 리뷰어 의견 + grep/test(11·13강). 예: Decimal 철칙은 `pension_calc.py`(전부 Decimal)를 grep으로 기계 검증.
5. **리뷰어도 틀린다**: 완벽한 하나는 없다 → 26강 적대적 다중화(cross-provider) 예고.

## 결정 2 — 변경 범위 4장치 (surgical)
- **공간**: worktree(`isolation: worktree`, reviewer.md) — 격리된 레포 복사본, 메인 오염 방지.
- **시간**: `/rewind`(코드만 복원). ⚠️ git 아님(bash rm·외부·타세션 미추적) → git·권한·샌드박스와 겹쳐서.
- **의도**: surgical 규칙(checklist.md 변경 범위 섹션 = 유도) + **`.claude/hooks/guard-diff-size.sh`(상한 강제)**. 규칙은 유도, 유도는 보장이 아니다(05강) → 파일 5·라인 300 초과면 exit 2(21강 표류 감독).
- **리뷰 범위**: `git diff --name-only`(13강, 변경 파일만).

## 결정 3 — 재견고화 루프
리뷰어를 일부러 뚫어(예외 처리 확장으로 차단 경로 우회 diff) 놓친 패턴을 checklist.md에 한 줄 추가 → 같은 diff 재검증(이번엔 🔴). "뚫리면 규칙이 자란다"(11강)·14강 훅 뚫기의 리뷰어판·30강 파이널 채점 리허설. checklist.md에 그 한 줄이 실제로 들어갔다("예외 처리 범위가 넓어지는 변경은 차단 경로 우회 여부 확인").

## 결과 (`ch4-25-done`)
- 실물: `.claude/output-styles/reviewer.md` · `.claude/agents/reviewer.md`(isolation: worktree) · `.claude/skills/code-review/checklist.md`(강화) · `.claude/hooks/guard-diff-size.sh` + 테스트. 72 passed · PASS 6/6.
- 🟡(커리큘럼 "아키텍처 위배 변경을 잡는 리뷰어") 해소: checklist에 "요청에 없는 import·모듈 경계 위반" 필수 체크 → 30강 아키텍처 가드로 자란다.
