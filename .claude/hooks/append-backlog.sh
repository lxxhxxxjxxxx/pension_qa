#!/usr/bin/env bash
# 27강 — 자동 백로그. 리뷰가 끝나는 순간 🟡 Nit·🟣 Pre-existing 을 BACKLOG.md 로 흘려보낸다.
#   사람 기억에 맡기면 증발한다 — 부채는 늘 바쁠 때 생기고, 그 순간 손으로 옮기는 건 빠진다.
#   Stop / SubagentStop 입력 JSON 의 last_assistant_message 를 읽는다(공식 hooks: transcript 대신 이 필드).
#   리뷰 산출이 아닌 턴이면 아무것도 안 하고 조용히 통과한다(exit 0).
#   ⚠️ 같은 이벤트의 훅은 전부 병렬로 돈다 — 21강 gate-pytest.sh 를 덮어쓰지 말고 배열에 나란히 둘 것.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
python3 scripts/append_backlog.py --from-stdin >/dev/null 2>&1 || true
exit 0
