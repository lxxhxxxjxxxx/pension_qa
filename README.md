> 📚 **강의 스냅샷 — 06강을 마친 상태입니다.**  
> 시작점 `ch1-06-start` → **지금 여기 `ch1-06-done`** → 다음 강 시작점 `ch1-07-start`

## 06강 · 요구사항 → 명세 → ADR-first

요구를 바로 코딩하지 않는다. plan → 인터뷰(SPEC) → ADR → 구현 → 검증 한 바퀴를 돈다.

**배우는 것**

- plan 모드로 먼저 읽고 계획만 세운다(수정 금지)
- `AskUserQuestion`으로 **제품 결정만** 인터뷰 — 구현 디테일은 묻지 않는다 → `SPEC.md`
- `/adr` 커맨드로 결정을 `docs/adr/`에 쌓는다. 결정을 채팅에 흘리지 않는다
- SPEC의 "통과 기준"으로 닫는다

**이 브랜치에 들어온 것**

- `SPEC.md` · `SPEC_score.md` — 명세 2건
- `.claude/commands/adr.md` — `/adr` 커맨드
- `docs/adr/0001-email-masking.md` · `0002-evidence-score-gate.md`
- 근거 커버리지 2단 임계 구현(0.15 보류 / 0.40 저신뢰) + 출력 이메일 마스킹 + 테스트

**확인해 보기**

```bash
git diff ch1-06-start..ch1-06-done --stat
python -m pytest -q        # 25 passed
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
