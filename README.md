> 📚 **강의 스냅샷 — 22강을 마친 상태입니다.**  
> 시작점 `ch3-22-start`(= `ch3-21-done`) → **지금 여기 `ch3-22-done`** → 다음 강 시작점 `ch3-23-start`(23강 준비 때 생성)

## 22강 · [실습] MCP 직접 연결 + 에러 처리

연결은 `claude mcp add` 한 줄이다. 어려운 건 그 다음 — 서버가 죽고 토큰이 만료되고 타임아웃이 날 때 우리 에이전트가 어떻게 행동하느냐. 18강(설계)과 20강(신뢰성)을 실제 연결 위에서 한 바퀴 돈다.

**배우는 것**

- 첫 연결은 읽기 전용 — 플래그가 아니라 **쓰기 도구의 부재**로(18강 스코프). `pension_qa_docs/server.py`는 `list_docs`·`read_doc`만 노출
- 실패 5종을 손으로 재현: 틀린 URL `✘ Failed to connect` · `--slow`+`MCP_TIMEOUT` startup 타임아웃 · 401(재시도 금지) · 404 감각(서버는 살아있음) · 스코프 불일치(`✔ Connected`인데 도구가 늘어남)
- 증상 → 분류 → 원인: `claude mcp list` 상태표 → `/mcp` → `claude --debug "api,mcp"` + stdio 직접 실행. 절차를 `TROUBLESHOOTING.md`로 커밋
- 20강 5요소를 MCP 호출에 (`app/mcp_client.py`) · 상한은 설정·훅으로 강제 — PreToolUse `mcp__.*` 훅(`guard-mcp.sh`)이 쓰기성 MCP 호출을 exit 2로 차단

**이 브랜치에 들어온 것**

- `pension_qa_docs/server.py` — mcp 2.x MCPServer(1.x FastMCP 호환) 미니 서버, `--slow`/`--with-write` 실습 스위치
- `TROUBLESHOOTING.md` — 진단 플레이북(증상→분류→원인, 상태표×1차조치)
- `.mcp.json` — `pension_qa-docs` 읽기전용(20강이 놓은 config를 실물 서버로) · `.claude/hooks/guard-mcp.sh` + settings `mcp__.*`(20강 `guard-external.sh`와 함께)
- `app/mcp_client.py` — MCP 호출 신뢰성 래퍼(타임아웃·분류 재시도·상한·폴백·로그) + 테스트
- `docs/adr/0007-mcp-connection-and-error-handling.md`

**확인해 보기**

```bash
pip install "mcp>=2,<3"                               # 서버 SDK (촬영 실측 mcp 2.1.1)
python3 -m pension_qa_docs.server                     # Claude 없이 서버 자체 기동(진단 치트키)
claude mcp add pension_qa-docs -- python3 -m pension_qa_docs.server
claude mcp list                                       # pension_qa-docs ... ✔ Connected
python3 -m pytest -q                                  # 61 passed (mcp 없으면 서버 테스트 skip)
echo '{"tool_name":"mcp__pension_qa-docs__write_doc"}' | bash .claude/hooks/guard-mcp.sh; echo $?   # 2 (쓰기 차단)
```

전체 강별 브랜치 지도는 [`main` 브랜치 README](../../tree/main#강의별-브랜치-지도)에 있습니다.
<!-- /강의안내 -->

> 📚 **강의 스냅샷 — 21강을 마친 상태입니다.**  
> 시작점 `ch3-21-start` → 끊긴 상태 `ch3-21-interrupted` → **지금 여기 `ch3-21-done`** → 다음 강 시작점 `ch3-22-start`(22강 준비 때 생성)

## 21강 · 장기 자율 작업의 6장치

사람이 매 턴을 보지 않는 자율 실행은 폭주·표류·유실로 무너진다. 여섯 장치를 전부 레포의 파일·설정으로 두고, 밤에 끊긴 자율 작업을 새 세션이 로그만 읽고 이어가게 했다.

**배우는 것**

- 성공 기준은 기계가 판정한다 — `docs/autonomy/작업로그.md`의 `성공기준` 줄 = `python3 -m pytest -q` 초록. `/goal`은 작은 모델이 대화를 보고 판정하므로 여기선 쓰지 않는다
- 14강 Stop 훅에 연속 차단 상한(`GATE_MAX_BLOCKS=3`)을 얹었다 — 영영 못 맞추는 테스트면 막지 않고 사람에게 넘긴다(HITL)
- `--dangerously-skip-permissions`는 컨테이너 안에서만 — `scripts/autorun.sh`가 밖에서는 거부하고 allowlist로 좁혀 돈다
- 격리는 범위, 상한은 양 — `--max-turns` · `--max-budget-usd` · `MAX_THINKING_TOKENS`
- 상태는 대화가 아니라 로그와 커밋에 — 세션 전사가 없어도 새 세션이 이어간다

**이 브랜치에 들어온 것**

- `.claude/hooks/gate-pytest.sh` + `.claude/settings.json` Stop → 스크립트 — 상한 · 로그 흔적 · HITL 인계
- `scripts/autorun.sh` · `scripts/autorun_render.py` — 자율 실행 한 줄 + 턴·도구·게이트를 보이는 관측 렌더러
- `docs/autonomy/작업로그.md` — 작업 · 성공기준 · 진행 · HITL 경계 · 이력(자율 실행이 남긴 줄 그대로)
- `app/guardrails.py` `check_output_disclaimer` + `tests/test_guardrails.py` 3건 — **자율 실행이 만든 산출물**(`ch3-21-run1`: 11턴 · 82초 · $0.86, run2·run3도 초록)
- `docs/adr/0006-autonomous-run-safeguards.md`

**확인해 보기**

```bash
git diff ch3-21-start..ch3-21-interrupted --stat   # 6장치 세팅 + red 테스트 = 끊긴 상태
git diff ch3-21-interrupted..ch3-21-done --stat    # 자율 실행이 만든 것
python3 -m pytest -q                               # 49 passed
bash scripts/autorun.sh --dry-run                  # 컨테이너 밖 → allowlist 모드
echo '{"session_id":"x"}' | bash .claude/hooks/gate-pytest.sh; echo $?   # 초록이면 0
```

전체 강별 브랜치 지도는 [`main` 브랜치 README](../../tree/main#강의별-브랜치-지도)에 있습니다.
<!-- /강의안내 -->

> 📚 **강의 스냅샷 — 20강을 마친 상태입니다.**  
> 시작점 `ch3-20-start` → **지금 여기 `ch3-20-done`** → 다음 강 시작점 `ch3-21-start`(21강 준비 때 생성)

## 20강 · 외부 호출 신뢰성 5요소

외부는 항상 실패한다. 견디게 만드는 다섯 — 타임아웃 · 재시도(분류·상한) · 멱등성 · 폴백 · 관측 — 를 우리 봇의 가장 크고 비싼 외부 의존인 LLM 호출에 입히고, 상한을 모델이 아니라 설정·훅으로 강제한다.

**배우는 것**

- `llm.py`의 폴백 한 줄은 반쪽 신뢰성 — 타임아웃·재시도·관측이 없어 하루에 몇 번 실패하는지 아무도 몰랐다
- 재시도는 분류해서(429·5xx·타임아웃만) 상한 안에서 — 상한이 곧 비용 캡. 401·404는 즉시 폴백
- `MCP_TIMEOUT`(연결/시작) vs `MCP_TOOL_TIMEOUT`(호출 응답)은 별개 노브 — 둘 다 `settings.json` env에 고정
- 신뢰성은 모델이 기억하는 게 아니라 시스템이 강제하는 것 — PreToolUse `mcp__.*` 훅이 정책 없는 외부 호출을 exit 2로 차단

**이 브랜치에 들어온 것**

- `app/llm.py` — 타임아웃 명시(`LLM_TIMEOUT_S`) · 분류 재시도(`RETRYABLE`) · 상한(`LLM_MAX_RETRIES`) · `Retry-After` 존중 · 지수 백오프+지터 · 모든 갈림길 로그 · 기존 폴백 유지
- `tests/test_llm.py` — 8건(타임아웃 명시 · 재시도 후 성공 · 타임아웃 재시도 · 401 즉시 폴백 · 상한=비용 캡 · 429 Retry-After · 폴백 로그 · stub)
- `.claude/settings.json` — `env: MCP_TIMEOUT=3000 · MCP_TOOL_TIMEOUT=10000` + PreToolUse `mcp__.*` → `.claude/hooks/guard-external.sh`
- `.claude/hooks/guard-external.sh` — 타임아웃 정책 없으면 exit 2(stderr가 Claude에 피드백)
- `docs/adr/0005-external-call-reliability.md` — 정책 결정 기록

**확인해 보기**

```bash
git diff ch3-20-start..ch3-20-done --stat        # 무엇이 들어왔나
python -m pytest tests/test_llm.py -q            # 8 passed
python -m pytest -q                              # 46 passed
env -i bash .claude/hooks/guard-external.sh; echo $?                              # 2 (정책 없음 → 차단)
MCP_TIMEOUT=3000 MCP_TOOL_TIMEOUT=10000 bash .claude/hooks/guard-external.sh; echo $?   # 0
```

전체 강별 브랜치 지도는 [`main` 브랜치 README](../../tree/main#강의별-브랜치-지도)에 있습니다.
<!-- /강의안내 -->

# pension_qa — 연금 안내 Q&A 에이전트

사용자의 연금(연금저축·IRP·연금소득세) 질문에 **사내 연금 가이드 문서를 검색(RAG)** 해서 근거와 함께 답하는 작은 LLM 프로덕트.

> ⚠️ 클린룸 예제입니다. 모든 문서·코드는 강의용으로 새로 작성한 **가상** 데이터이며 실제 사내 시스템과 무관합니다.

## 동작

```
질문 → [입력 가드레일] → 문서 검색 → LLM 답변 → [출력 가드레일] → 답변+근거
```

## 실행

```bash
pip install -r requirements.txt
python -m app.main "연금저축 세액공제 한도가 얼마인가요?"
```

`ANTHROPIC_API_KEY`가 없으면 LLM 호출은 stub 응답으로 대체됩니다(검색·가드레일은 그대로 동작).

## 구조

- `app/retriever.py` — 문서 검색(단순 키워드 스코어)
- `app/guardrails.py` — 입력(PII·범위)·출력(유출) 가드레일
- `app/llm.py` — LLM 클라이언트(Anthropic, 없으면 stub)
- `app/agent.py` — 오케스트레이션
- `app/pension_calc.py` — 연금 계산 유틸(Decimal 전용 — 아직 답변 파이프라인 미연결)
- `data/` — 가상 연금 가이드
- `tests/` — 샘플 테스트

## TODO (알려진 거친 부분)

- 가드레일이 stub 수준(정규식 몇 개) — 범위·유출 판정이 허술함
- 테스트 커버리지 얕음
- 검색이 단순 토큰 겹침(임베딩 아님)
- 계산 유틸이 답변 파이프라인에 연결돼 있지 않음
- 빌드·컨벤션·아키텍처 문서 없음
