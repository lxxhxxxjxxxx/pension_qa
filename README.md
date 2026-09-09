> 📚 **이 레포는 강의 「AI 엔지니어를 위한 프로덕트 엔지니어링」의 실습 레포입니다.**
> `main`은 **아무것도 깔리지 않은 출발점**(빈 `.claude/`)입니다. 강별로 브랜치가 있습니다.

## 강의별 브랜치 지도

각 강의 **끝점** 브랜치를 체크아웃하면 그 강을 마쳤을 때 레포가 어떤 상태인지 그대로 보입니다.
브랜치를 옮기면 이 README 맨 위 안내도 그 강 내용으로 바뀝니다.

```bash
git clone git@github.com:lxxhxxxjxxxx/pension_qa.git && cd pension_qa
git checkout ch1-05-done      # 05강까지 마친 상태
git diff ch1-05-start..ch1-05-done --stat    # 05강이 뭘 채웠는지
```

**시작점 = 직전 강의 끝점**입니다. 07강부터 해보고 싶으면 `ch1-07-start`(= `ch1-06-done`)를 체크아웃하세요.

| 강 | 시작점 | 끝점 | 이 강이 레포에 채우는 것 | pytest |
|---|---|---|---|---|
| 01 순정 페인포인트·5 구성요소 | `ch1-01-start` | `ch1-01-done` | — 개념강(빈 `.claude/`가 교재) | 11 |
| 02 주입 컨텍스트 CLAUDE.md | `ch1-02-start` | `ch1-02-done` | `CLAUDE.md` 4덩어리 | 11 |
| 03 문서 하네스화 | `ch1-03-start` | `ch1-03-done` | `.claude/rules/guardrails.md` · `@import` | 11 |
| 04 memory 협업 사고 | `ch1-04-start` | `ch1-04-done` | CLAUDE.md 컨벤션 한 줄(메모리→커밋되는 곳) | 11 |
| 05 암묵 제약 명시화 | `ch1-05-start` | `ch1-05-done` | `.claude/settings.json` permissions · `secrets/` | 11 |
| 06 요구→명세→ADR-first | `ch1-06-start` | `ch1-06-done` | `SPEC*.md` · `/adr` · ADR 0001·0002 · 근거 게이트 | 25 |
| 07 서브에이전트 4역할 | `ch1-07-start` | `ch1-07-done` | `.claude/agents/` 4개 · 입력 마스킹 구현 | 31 |
| 08 [파이널] 하네스 구축 | `ch1-08-start` | `ch1-08-done` | 용어집·결정 기록 규칙 · `harness_check.sh` · ADR 0003 | 31 |
| 09 [안티패턴] 개발 단계 진단 | `ch1-08-done` | `ch2-09-done` | — 진단강(실측은 `ch2-09-*`) | 31 |
| 10 [페인포인트] 레거시 답습 | `ch2-09-done` | `ch2-10-done` | — 진단강(실측은 `ch2-10-*`) | 31 |
| 11 hallucination 6패턴 | `ch2-11-start` | `ch2-11-done` | — 개념·실측강(`ch2-11-sanitize-run*`) | 31 |
| 12 Skills 기본 | `ch2-12-start` | `ch2-12-done` | — 개인 스코프 스킬(`~/.claude/skills/`) | 31 |
| 13 [실습] 코드리뷰 Skill | `ch2-12-done` | `ch2-13-done` | `.claude/skills/code-review/` | 31 |
| 14 Hooks 안전장치 | `ch2-14-start` | `ch2-14-done` | settings.json hooks 3종 + deny | 31 |
| 15 테스트 품질 · mutation | `ch2-15-start` | `ch2-15-done` | `setup.cfg` · 테스트 보강 · ADR 0004 | 38 |
| 16 [파이널] 버그 PR 자동 적발 | `ch2-16-start` | `ch2-16-done` | 버그 PR을 4겹으로 적발(촬영 후 fail-closed 테스트 보강 커밋 예정) | 38 |
| 17 [안티패턴] 통합 단계 진단 · 샌드박스 | `ch3-17-start` | `ch3-17-done` | — 개념·시연강(샌드박스는 `settings.local.json`) | 38 |
| 18 MCP 서버 설계와 보안 | `ch3-18-start` | `ch3-18-done` | `.mcp.json` 읽기 전용 문서 서버(서버 코드는 22강) | 38 |
| 19 [페인포인트] 핫픽스 컨텍스트 손실 | `ch3-19-start` | `ch3-19-done` | `HOTFIX.md` 5줄 카드(완화 절차화) | 38 |
| 20 외부 호출 신뢰성 5요소 | `ch3-20-start` | `ch3-20-done` | `llm.py` 하네스(타임아웃·분류 재시도·상한·로그) · `test_llm.py` 8 · settings env + `mcp__.*` 훅 · ADR 0005 | 46 |
| 21 장기 자율 작업의 6장치 | `ch3-21-start` | `ch3-21-done` | 6장치 세팅(`gate-pytest.sh` 상한·HITL · `autorun.sh` 격리 분기·상한 · `작업로그.md` · ADR 0006) + 자율 실행이 만든 `check_output_disclaimer` · 끊긴 상태 `ch3-21-interrupted` · 실측 `ch3-21-run1~3`·`-cap` | 49 |
| 22 [실습] MCP 직접 연결 + 에러 처리 | `ch3-22-start` | `ch3-22-done` | `pension_qa_docs/server.py`(읽기전용 문서 MCP 서버, mcp 2.x) · `app/mcp_client.py`(신뢰성 5요소 래퍼) · `.claude/hooks/guard-mcp.sh`(쓰기 도구 exit 2) · `.mcp.json` · `TROUBLESHOOTING.md` · ADR 0007 | 61 |
| 23 [Ch3 파이널] 배포현황 봇 | `ch3-23-start` | `ch3-23-done` | `app/deploy_bot.py`(구조화 필드 요약=인젝션 방어·5요소·멱등·폴백) · `scripts/`(mock_events·run_deploy_bot·**grade_bot PASS 5/5**) · ADR 0008 · 나가는 게이트=mcp__.* 훅 재사용 | 66 |
| 24 [Ch4 시작] 운영 안티패턴 진단 | `ch4-24-start` | `ch4-24-done` | `docs/adr/0009-incident-response.md`(장애대응 ADR) · `docs/runbook/운영진단표.md` · `tests/test_incident_response.py`(재발방지 회귀) · `.claude/settings.json` `env`(OTel) · `hooks/audit-config-change.sh`+`ConfigChange` 훅+테스트 · CLAUDE.md 운영 규칙 | 72 |
| 25 리뷰어 견고화 + 변경 범위 제어 | `ch4-25-start` | `ch4-25-done` | `.claude/output-styles/reviewer.md` · `agents/reviewer.md`(포맷 본문 내장, worktree 없음) · `code-review/checklist.md` 강화 · CLAUDE.md surgical 규칙 · `hooks/guard-diff-size.sh`+테스트+**settings.json PreToolUse 등록**(상한 exit 2) · ADR 0010 | 75 |
| 26 적대적 리뷰어 다중화 + 결정적 집계 | `ch4-26-start` | `ch4-26-done` | `agents/reviewer-{accuracy,security,perf}.md`(렌즈별·포맷 본문 내장·worktree 없음) · `scripts/aggregate_reviews.py`+mock(≥2표·1표+기계증거·논파 폐기) · `tests/test_aggregate_reviews.py`(8) · ADR 0011 · harness ④ 진화 | 83 |
| 27 기술부채 정량추적 + 자동 백로그 + 큐 분리 | `ch4-27-start` | `ch4-27-done` | (이름 선점 2026-09-09 — 코드는 시작점과 동일, 안내 README만. 부채 스캔·백로그 append 훅·`BACKLOG.md`·큐 라우팅은 수정 패스·촬영 뒤 fast-forward) | 83 |

> 09·10·13강은 시작점 브랜치 이름이 촬영용으로 먼저 쓰이고 있어서, 표의 직전 끝점을 그대로 쓰면 됩니다.

### 실습·비교용 브랜치 (본 체인과 별개)

같은 요청을 여러 번 돌린 **실측 결과**나, 리뷰·디버깅 연습용 상태입니다.

| 브랜치 | 쓰임 |
|---|---|
| `ch2-09-start` · `ch2-09-run1~3` · `-alt-noverify` · `-alt-noharness` | 09강 — 같은 요청 3회가 갈리는 실측(+ 조건이 다른 별건 2종) |
| `ch2-10-start` · `run1~3` · `control` · `subtle-*` · `harness-*` | 10강 — 레거시 주입/대조군/미묘 패턴/하네스 유무 |
| `ch2-11-sanitize-run1~3` | 11강 — 같은 프롬프트 3회, 접근·변경량·테스트 수가 전부 다름 |
| `ch2-13-start` · `ch2-13-pr` | 13강 — 리뷰 대상 나쁜 PR 3종. `git diff HEAD~1`로 본다 |
| `ch2-14-buggy` | 14강 — `tax_credit` 한도 미적용 버그(`1 failed, 10 passed`) |
| `ch2-16-buggy` | 16강 — 근거 문서에 **낡은 한도(700만)** 가 심긴 상태. 테스트·grep·mutation 어디에도 안 걸린다(`38 passed`) — 판단 버그가 게이트를 통과하는 걸 보이는 용도 |
| `ch1-08-final` | 08강 통합 빌드(체인이 아니라 `ch1-start`에서 재구축한 별도 히스토리) |

### 환경

```bash
pip install -r requirements.txt
pip install pytest            # requirements.txt에는 없다
python -m pytest -q
```

14강은 `black`, 15강은 `mutmut coverage`가 추가로 필요합니다.

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
