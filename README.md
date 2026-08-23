> 📚 **강의 스냅샷 — 08강을 마친 상태입니다.**  
> 시작점 `ch1-08-start` → **지금 여기 `ch1-08-done`** → **09강도 이 브랜치에서 시작**

## 08강 · [파이널] 문서 없는 레포에 컨텍스트 하네스 구축

Ch1 전체를 한 세션에 통합하고, **사람 판단 0인 채점 스크립트**로 닫는다.

**배우는 것**

- CLAUDE.md · rules · settings · agents · ADR 다섯을 한 레포에 겹쳐 쌓는다
- 도메인 용어집이 설계 제안이 도메인 밖으로 튀는 걸 잡는 기준선이 된다
- `harness_check.sh` = 결정적 채점 첫 점등 — grep·ls만으로 6항목 판정
- 체크리스트 5개에 체크 안 되면 그 레포는 아직 "빈 `.claude/`"다

**이 브랜치에 들어온 것**

- `CLAUDE.md` 도메인 용어집 + 결정 기록 규칙
- `harness_check.sh` — PASS 6/6
- `docs/adr/0003-guardrail-architecture.md`

**확인해 보기**

```bash
bash harness_check.sh      # PASS 6/6
python -m pytest -q        # 31 passed
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
