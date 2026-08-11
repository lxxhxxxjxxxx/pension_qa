# pension_qa — 연금 안내 Q&A 에이전트

사용자의 연금(연금저축·IRP·연금소득세) 질문에 **사내 연금 가이드 문서를 검색(RAG)** 해서 근거와 함께 답하는 작은 LLM 프로덕트.

> ⚠️ 클린룸 예제입니다. 모든 문서·코드는 강의용으로 새로 작성한 **가상** 데이터이며 실제 사내 시스템과 무관합니다.

## 동작

```
질문 → [입력 가드레일: PII·범위] → [이메일 마스킹] → 문서 검색
     → [근거 게이트: 보류 / 저신뢰 / 정상] → LLM 답변 → [출력 가드레일: 유출·마스킹] → 답변+근거
```

근거가 부실하면 LLM을 부르지 않고 보류(`⛔`)하거나 저신뢰(`⚠️`)로 표시한다 — [ADR 0002](docs/adr/0002-evidence-score-gate.md)·[ADR 0003](docs/adr/0003-idf-weighted-retrieval.md).
질문에 적힌 이메일은 차단하지 않고 마스킹하며, 검색·LLM에는 마스킹본만 넘어간다 — [ADR 0001](docs/adr/0001-email-masking.md)·[SPEC.md](SPEC.md).

## 실행

```bash
pip install -r requirements.txt
python -m app.main "연금저축 세액공제 한도가 얼마인가요?"
```

`ANTHROPIC_API_KEY`가 없으면 LLM 호출은 stub 응답으로 대체됩니다(검색·가드레일은 그대로 동작).

## 구조

- `app/retriever.py` — 문서 검색(IDF 가중 토큰 스코어) + 근거 커버리지 산출
- `app/guardrails.py` — 입력(PII·범위)·출력(유출) 가드레일
- `app/llm.py` — LLM 클라이언트(Anthropic, 없으면 stub)
- `app/agent.py` — 오케스트레이션
- `app/pension_calc.py` — 연금 계산 유틸(Decimal 전용 — 아직 답변 파이프라인 미연결)
- `data/` — 가상 연금 가이드
- `tests/` — 샘플 테스트

## TODO (알려진 거친 부분)

- 입력 범위(scope)·출력 유출 판정이 아직 키워드·정규식 stub — 이메일 마스킹과 근거 게이트만 결정적으로 다듬어져 있음
- 검색이 IDF 가중 토큰 겹침이라 어휘가 어긋나면 못 찾음(임베딩·형태소 분석기 미도입) — `연령` 문서에 `나이`로 물으면 놓친다
- 근거 게이트 임계값이 `data/` 3개 문서 실측에 묶여 있음 — 문서가 늘면 재캘리브레이션 필요
- 계산 유틸이 답변 파이프라인에 연결돼 있지 않음
