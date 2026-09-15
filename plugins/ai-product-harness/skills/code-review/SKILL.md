---
name: code-review
description: 변경된 코드를 pension_qa 규칙으로 리뷰하고, 기계가 판정한 위반만 수정한다.
argument-hint: <branch-or-path>
disable-model-invocation: true
---

## 리뷰 대상 diff
!`git diff $ARGUMENTS`

## 결정적 검증 (실제 실행 결과)
!`grep -rEn "except\s*:" app/ || echo "OK: bare except 없음"`
!`grep -rn "float(" app/ || echo "OK: 금액 경로에 float 없음"`
!`python -m pytest -q 2>&1 | tail -3`

## 지시
전체 기준은 ${CLAUDE_SKILL_DIR}/checklist.md 를 따른다.

1. 위 diff를 checklist 기준으로 리뷰한다. **checklist의 심각도 정의에 없는 지적은 리포트에 넣지 않는다.**
2. 판정 근거는 diff 라인 또는 위 게이트 실행 결과로 댄다(느낌 금지).
3. 리포트는 정확히 세 섹션으로만 낸다: `## Important (머지 전 수정)` / `## 사람 확인 필요` / `## Nit`
4. **수정 라우팅** — Important 중 *기계가 판정한 형식 위반*(위 게이트가 매칭했거나 pytest가 실패한 것)만
   직접 수정한다. 고칠 때는 **그 지점이 checklist의 fail-closed·이유 반환 규칙까지 만족하도록** 고친다
   (매칭된 토큰만 바꾸고 멈추지 않는다). 로직·도메인 판단이 필요한 지적은 **고치지 말고** `사람 확인 필요`에 남긴다.
5. 수정했다면 `python -m pytest -q`를 다시 돌려 결과를 보고한다.
