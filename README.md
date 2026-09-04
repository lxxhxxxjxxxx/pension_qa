> 📚 **강의 스냅샷 — 18강을 마친 상태입니다.**  
> 시작점 `ch3-18-start` → **지금 여기 `ch3-18-done`** → 다음 강 시작점 `ch3-19-start`(19강 준비 때 생성)

## 18강 · MCP 서버 설계와 보안

MCP 연결은 기능 추가가 아니라 **신뢰 경계 설정**. 읽기 전용 문서 서버 하나를 `.mcp.json`으로 팀에 공유하고, 승인 게이트·시크릿 격리·조직 통제·감사 로그로 17강의 다섯 문제를 설계로 막는다.

**배우는 것**

- add 하는 순간이 곧 스코프를 정하는 순간 — `--read-only`
- `.mcp.json` = config-as-code. clone해도 자동 실행되지 않고 첫 진입 때 승인을 묻는다(기본 선택 = 거부 · `claude mcp reset-project-choices`로 되돌림). 단 `claude -p` 비대화형은 묻지 않는다
- 토큰은 `env`에 `${PENSION_QA_MCP_TOKEN}` 참조만 — 값은 셸에
- 조직 통제는 `serverCommand`로(이름은 라벨) · deny 우선 · 감사 로그는 PostToolUse `mcp__.*` 훅

**이 브랜치에 들어온 것**

- `.mcp.json` — `pension_qa-docs` stdio 서버(`python3 -m pension_qa_docs.server --read-only`, env 참조). **서버 코드는 22강에서 만든다** — 지금 체크아웃하면 `claude mcp list`에 `⏸ Pending approval`, 승인해도 `✘ Failed to connect`가 정상.

**확인해 보기**

```bash
python -m pytest -q                # 38 passed
claude mcp list                    # pension_qa-docs … ⏸ Pending approval (run `claude` to approve)
claude mcp get pension_qa-docs     # Environment: PENSION_QA_MCP_TOKEN=${PENSION_QA_MCP_TOKEN}
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
