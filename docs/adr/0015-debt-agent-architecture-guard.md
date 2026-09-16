# ADR 0015 — 마지막 두 조각: 부채 에이전트(자율화)와 아키텍처 가드(경화)

- 상태: 채택 (30강 · 코스 파이널)
- 맥락: 0001~0014 로 리뷰어(0010·0011)·부채 큐(0012)·플러그인 배포(0013)·자가점검(0014)까지 다 쌓였다. 그런데 전부 **사람이 방아쇠를 당겨야** 돈다 —
  `scan_debt.py` 도 `harness_review.sh` 도 사람이 치고, 아키텍처 규칙("guardrails 는 llm 을 부르지 않는다", 0003)은 체크리스트 한 줄(부탁)이라
  `from . import llm` 한 줄이면 뚫린다. 바쁘면 제일 먼저 버려지는 게 이 습관들이다(0009 운영 안티패턴).

## 결정 1 — 방아쇠를 사람에게서 뗀다, 그러나 훅과 스케줄러를 섞지 않는다 (`scripts/debt_agent.sh`)

공식 hooks·sub-agents 문서(2026-09-15): 훅은 **서브에이전트를 부르지 못하고**, 스케줄도 없다. 그래서 둘로 나눈다.
- **이벤트 → 결정적 스크립트**: `SessionStart` 훅(`.claude/hooks/debt-agent-session.sh`)이 세션마다 `debt_agent.sh --quiet`(스캔 → `BACKLOG.md` 갱신 → 요약)를 돌린다.
  0012 의 Stop 훅(`append-backlog.sh`)과 같은 문법 — 훅이 방아쇠, 몸통은 스크립트.
- **주기 → 스케줄러 → 에이전트**: `.claude/loop.md`(세션 안 `/loop`, 7일 만료) · `docs/ci/debt-agent.yml`(GitHub Actions `schedule`)이 `@debt-scanner` 를 부른다.
  0014 의 루틴(`harness_review.sh`)도 같은 자리에 얹는다(`--review`) — 사람 캘린더에 걸면 깜빡한다(0014 §4).

## 결정 2 — 감시자는 고치지 않는다, 그리고 그건 유도가 아니라 훅이다 (`.claude/agents/debt-scanner.md`)

`tools: Read, Grep, Bash` 는 쓰기 금지가 아니다 — Bash 가 있으면 `sed -i`·`>` 로 파일을 고친다(공식 sub-agents). 07강 "Write 없음 = 역할 강제"는 유도였다.
보장은 프론트매터 `hooks: PreToolUse` `matcher: Bash` → `.claude/hooks/guard-readonly-bash.sh`(허용목록 밖 명령·쓰기 통로 exit 2). 자율화 조각 안에 경화가 한 번 더.

## 결정 3 — 상환은 별도 에이전트가 한 항목 한 커밋으로, 검문은 기계가 먼저 (`debt-repayer` · `repay_gate.sh` · `record_repayment_adr.py`)

0012 의 자동 큐(저위험 ∧ 가역 ∧ 테스트 격리, 기계 판정)만 `@debt-repayer` 가 갚는다 — 브랜치 `repay/<file>-<line>`, 커밋 하나, PR 까지. 머지 전 검문:
① 그 파일 하나 ② surgical 상한(0010, 1파일·60줄) ③ 아키텍처 규칙(결정 4) ④ 테스트 초록 ⑤ 자동 큐 항목인가. 5/5 만 머지 가능.
그 위에 확률적 층(0010·0011 리뷰어, `/code-review`)이 한 층 더 — 기계 검문은 리뷰어를 대신하지 않고, 리뷰어가 못 하는 '기계 확인'만 한다.
결정은 `record_repayment_adr.py` 가 ADR 로 자동 기록하고 백로그를 체크한다(같은 file:line 은 다시 스캔돼도 [x] 보존 — 0012 병합 규칙). 되돌리기는 커밋 하나 revert.

## 결정 4 — 아키텍처 규칙은 두 층에서 같은 규칙표로 (`scripts/check_architecture.py` · `.claude/hooks/guard-architecture.sh`)

규칙은 지어낸 게 아니라 `app/*.py` 의 실제 import 구조(0003)에서 나왔다 — 레이어 위반(guardrails → llm) · 의존 방향(leaf → agent·main) · 금지 import(결정적 계층에 네트워크·LLM).
- **훅 층**: `PreToolUse Edit|Write` — 들어올 내용을 검사, 위반이면 exit 2 라 편집이 파일에 닿지 않는다. `PostToolUse` 는 이미 닿은 뒤라 못 막는다(공식). 훅 입력 `file_path` 는 **절대 경로** — basename 으로 본다. JSON 은 python3 로 읽는다(jq 는 없다고 가정).
- **파일 층**: 같은 규칙을 파일에 — CI 사전 머지 게이트·채점. 로컬 훅은 내 세션의 Edit/Write 만 보므로 동료의 PR·Bash `sed -i` 는 이 층이 막는다. 벽이 아니라 층(14강).
- **규칙은 자란다(25강)**: 2026-09-15 라이브에서 두 줄 `import importlib` / `importlib.import_module("app.llm")` 이 규칙 1 을 통과했다(grep 은 텍스트만 본다). 함수 안 지연 import 는 잡힌다(줄 단위).
  → 규칙 4(결정적 계층에서 동적 import 자체 금지)를 규칙표에 추가한다 — 채점 ④.

## 결정 5 — 코스의 마지막 채점 (`scripts/grade_final.sh`, PASS 4/4)

① 측정 재현(스캔 2회 JSON 동일) ② 자동 큐 전부 3조건 ✓✓✓ ③ 위반 주입 → 훅 exit 2 + 파일 층 🔴(긴급 큐 — 0012 라우팅: Important 는 백로그가 아니라 머지 차단) ④ 두 줄 importlib 변종이 규칙표에 막히나.
08강 `harness_check.sh` 6/6 · 23강 `grade_bot.sh` 5/5 · 29강 `harness_probe.sh` 5/5 와 같은 문법 — 코스의 마지막 화면도 사람 박수가 아니라 기계의 PASS.

## 결과·트레이드오프

- 세션마다 스캔이 돈다(pytest --cov ≈ 3초). 흔적은 `.claude/debt_agent.log`(gitignore) — 워킹트리를 더럽히지 않아 0014 프로브 조건(깨끗한 트리)을 지킨다.
- 상환 에이전트는 사람 큐를 받지 않는다 — `record_repayment_adr.py` 가 거부한다. 백로그 밖의 것을 갚았다면 그건 자동 상환이 아니다.
- 플러그인(0013)은 새 훅·에이전트를 나른다(1.1.0 → 1.2.0). 다른 레포에 깔리면 `debt-agent-session.sh` 는 `scripts/debt_agent.sh` 가 없어 조용히 통과한다.
