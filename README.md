> 📚 **강의 스냅샷 — 14강을 마친 상태입니다.**  
> 시작점 `ch2-14-start` → **지금 여기 `ch2-14-done`** → 다음 강 시작점 `ch2-15-start`

## 14강 · Hooks — 바닥을 올리는 안전장치

게이트를 **자동·무조건** 실행시킨다. "테스트 돌려"라고 안 했는데 통과가 보장된다.

**배우는 것**

- **exit 2만 차단**한다. exit 1은 비차단 — 실측으로 확인
- PostToolUse: 편집마다 포맷 / PreToolUse: 위험 명령 차단 / **Stop: 테스트 통과까지 턴 종료 차단**
- Stop 훅 명령 두 곳이 성패를 가른다 — `2>&1`(실패 내용을 stderr로 보여야 고친다) · `cd "$CLAUDE_PROJECT_DIR"`(훅은 모델 셸의 cwd를 물려받는다)
- 게이밍 방어: 테스트를 고쳐 초록불 만드는 우회는 `Edit(tests/**)` deny로 봉인
- 단일 훅은 뚫린다(Bash `rm`만 보면 `os.remove`로 우회) — **벽이 아니라 층**

**이 브랜치에 들어온 것**

- `.claude/settings.json` hooks 3종(PostToolUse · PreToolUse · Stop) + deny `Edit(tests/**)`

> 연습용 버그는 **`ch2-14-buggy`** — `tax_credit`에 한도 미적용(`1 failed, 10 passed`).
> 커밋 메시지는 `perf: tax_credit 한도 계산 단순화`로 성능 개선 PR처럼 보이게 해뒀다.

**확인해 보기**

```bash
python -m pytest -q        # 31 passed
# 훅 동작 확인 전 `pip install black pytest`
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
