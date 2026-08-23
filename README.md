> 📚 **강의 스냅샷 — 15강을 마친 상태입니다.**  
> 시작점 `ch2-15-start` → **지금 여기 `ch2-15-done`**

## 15강 · 테스트 품질 추적 — mutation score

14강이 보장한 "테스트 통과"가 **진짜인지** 검증한다. 라인 커버리지 100%인데 검증은 0일 수 있다.

**배우는 것**

- assert 없는 테스트도 커버리지는 100%를 만든다 — "실행됐나 ≠ 검증됐나"
- mutation testing: 코드에 작은 버그를 심고 테스트가 잡나 본다. survived = **약한 테스트의 정확한 위치**
- score를 결정적 게이트로(임계 80%). 느리니 핵심 모듈만·CI 주기로
- equivalent mutant 때문에 100%는 원래 불가 — 억지로 죽이면 문자열을 베끼는 **과적합 테스트**가 된다

**이 브랜치에 들어온 것**

- `setup.cfg` — mutmut `source_paths` + pytest `norecursedirs = mutants`
- `tests/test_guardrails.py` 보강 — 출력 유출 판정·차단 사유 검증(mutation 44/64 → **53/64, 82.8%**)
- `docs/adr/0004-mutation-gate.md` — 임계 80% 결정
- 14강 `Edit(tests/**)` deny 해제 — 테스트를 늘리는 게 이 강의 작업이라서

> ⚠️ `setup.cfg`의 `norecursedirs = mutants`가 없으면 `mutmut run` 뒤 평범한 `pytest`가 수집 에러로 죽고,
> **14강 Stop 훅이 영구 실패**한다. 이 브랜치는 그걸 넣은 상태다.

**확인해 보기**

```bash
pip install mutmut coverage
mutmut run "app.guardrails*"
mutmut results | grep survived   # 11개(전부 equivalent·문자열 변형)
python -m pytest -q        # 38 passed
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
