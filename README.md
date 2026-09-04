> 📚 **강의 스냅샷 — 16강을 마친 상태입니다.**  
> 시작점 `ch2-16-start` → **지금 여기 `ch2-16-done`** → 다음 강 시작점 `ch3-17-start`

## 16강 · [파이널] 버그 심긴 PR에서 문제 자동 적발

Ch2 전체(Skills·Hooks·게이트·mutation)를 합쳐, 버그 3종(fail-open 회귀·가짜 import·sources 누락)이 심긴 PR을 네 겹으로 자동 적발한다. 게이트가 못 잡는 판단 버그 1종은 사람 큐로 보낸다.

**배우는 것**

- 한 PR을 스킬(`/code-review`)·reviewer 서브에이전트·Stop 훅(pytest)·mutation 네 겹이 각각 어디서 잡는지
- 근거 문서에 심긴 판단 버그(세액공제 한도 700만)는 네 겹 전부 통과한다 — `ch2-16-buggy`(`38 passed`)
- Ch2 게이트 체크리스트 — 무엇이 결정적으로 막히고 무엇이 사람 몫인지

**이 브랜치에 들어온 것**

- 코드는 `ch2-16-start`(= `ch2-15-done`)와 동일. 촬영에서 나오는 fail-closed 테스트 보강은 촬영 뒤 이 브랜치에 커밋으로 얹는다(fast-forward).

**확인해 보기**

```bash
python -m pytest -q                    # 38 passed
bash harness_check.sh                  # PASS 6/6
git diff ch2-16-start..ch2-16-buggy    # 판단 버그 D — 근거 문서 한 곳
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
