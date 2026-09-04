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
