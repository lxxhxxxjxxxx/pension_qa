#!/usr/bin/env bash
# 30강 — 부채 에이전트의 이벤트 방아쇠(SessionStart). 세션이 열릴 때마다 스캔·백로그를 갱신하고 요약을 컨텍스트에 넣는다.
#   훅은 서브에이전트를 부르지 못한다(공식) — 그래서 여기서 도는 건 결정적 스크립트다. 판단이 드는 상환은 @debt-repayer(사람 또는 스케줄러가 부른다).
#   stdout 은 SessionStart 에서 Claude 의 컨텍스트로 들어간다 — 세션 첫 화면에 "자동 상환 후보 N건"이 뜬다.
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
[ -f scripts/debt_agent.sh ] || exit 0          # 플러그인으로 다른 레포에 깔린 경우 — 조용히 통과
bash scripts/debt_agent.sh --quiet 2>/dev/null || true
exit 0
