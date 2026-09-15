# ADR 0014 — 하네스도 코드다: 정기 자가점검·내구성 프로브·KPI 두 단계

- 상태: 채택 (29강)
- 맥락: 0001~0013 으로 하네스를 쌓고 28강에서 플러그인으로 팀에 배포했다. 그 하네스는 만든 날엔 코드베이스에 정확히 맞는다.
  그러나 코드는 계속 바뀌고 하네스는 안 바뀐다 — 실제로 13강에서 넣은 `code-review` 스킬의 결정적 검증
  `grep -rn "float(" app/` 은 20강이 `app/llm.py` 에 타임아웃 `float(` 을 넣은 뒤 **매 리뷰마다 두 줄을 경고**했고,
  "OK: 금액 경로에 float 없음" 분기엔 그 뒤 한 번도 가지 못했다. 항상 경고하는 게이트는 항상 통과하는 게이트와 같다 — 아무도 안 본다.
  27강이 코드 부채를 숫자로 쟀다면 이건 **하네스 부채**다.

## 결정 1 — 여섯 칸을 근거로 판정한다 (`scripts/harness_audit.py`)

CLAUDE.md(경로 실재) · 게이트(`harness_check.sh` + 스킬 `!` 줄을 실제 실행, 규칙 밖 모듈에서만 경고하면 ⚠️) · 스킬(OTel
`skill_activated`·`user_prompt.command_name`) · 훅(settings ↔ 스크립트 실재·실행권한, `hook_registered`, BACKLOG·작업로그 흔적) ·
서브에이전트(model 필드, `cost.usage` `agent.name`) · 플러그인(`build_plugin --check`, version 이후 `.claude/` 커밋).
판정 규칙은 스크립트에 고정 — 같은 레포·같은 로그면 같은 판정. 근거가 없는 칸은 ⚪로 남긴다(지어내지 않는다).

## 결정 2 — 게이트 자체를 테스트한다 (`scripts/harness_probe.sh`)

일부러 나쁜 것을 넣고 게이트가 막나 본다(16강을 정기 루틴으로): 금액 경로 float · 답변 속 주민번호 · bare except · 빨간 테스트 → Stop ·
와이드 diff → PreToolUse. 다섯 전부 되돌린다. 죽은 게이트는 사고가 나기 전엔 안 보인다 — 그래서 사고 전에 찔러 본다.

## 결정 3 — KPI 는 두 단계 (`scripts/harness_kpi.py`)

프록시(적발률·작업당 비용·usage)는 게이밍된다(마구 지적하면 적발률↑). 위에 결과 지표(오탐률·MTTD·MTTR)를 둔다.
오탐률은 26강 검증 결과에서 바로 나온다(refuted 1/3). MTTD·MTTR 은 장애 ADR 에 `- 발생:`·`- 발견:`·`- 복구:` 시각이 있어야
나온다 — 0009 엔 없으므로 "미기록"으로 뜬다. **미기록은 0이 아니다** — 다음 장애부터 시각을 남긴다.

## 결정 4 — 루틴 한 명령 (`scripts/harness_review.sh`)

자가점검 → KPI → 프로브 → 결정(사람) → 재배포(bump → `/plugin update`). `docs/runbook/하네스_리뷰_<날짜>.md` 로 남는다.
첫 실행의 결정: float 게이트를 규칙 범위(`app/pension_calc.py`·`app/agent.py`)로 좁히고 플러그인 **1.0.0 → 1.1.0**.

## 텔레메트리는 이미 켜져 있다 — 보는 방법이 문제

24강이 `settings.json` `env` 에 OTLP(`localhost:4317`)를 박아 뒀고 **그 값은 셸 env 를 이긴다**. collector 가 없으면
아무 데도 안 간다. 화면에서 보려면 `scripts/otel_console.py on`(`settings.local.json`, local > project) →
`claude -p "/code-review HEAD~1" 2>&1 | tee docs/otel/console.log`. 공식 문서 이벤트 표(2026-09-15)엔 `skill_activated` 가
없지만 2.1.272 는 찍는다 — `scripts/mock_otel_console.log` 가 그 원본이고 파서(`scripts/otel_log.py`)는 그 출력 형식을 읽는다.

## 내구성

담당자 이탈엔 "왜"(이 문서·CLAUDE.md), 시간엔 프로브, 모델 변화엔 두 층 — 결정적 층(grep·테스트·harness_check)은 모델 무관,
확률적 층(리뷰어·스킬 문장)만 재검증. 내일 다른 도구로 갈아타도 결정적 층과 텍스트 자산은 남는다 — 날아가는 건 훅 배선·플러그인 패키징뿐.
