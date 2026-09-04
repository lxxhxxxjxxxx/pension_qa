> 📚 **강의 스냅샷 — 19강을 마친 상태입니다.**  
> 시작점 `ch3-19-start` → **지금 여기 `ch3-19-done`** → 다음 강 시작점 `ch3-20-start`(20강 준비 때 생성)

## 19강 · [현업 페인포인트] 핫픽스 중 컨텍스트 손실

급할수록 하네스가 무너진다. 긴급 핫픽스에서 세션이 길어져 자동 compaction이 초반 제약을 버리고, "로드돼 있겠지" 전제가 깨지고, 급하다고 게이트를 건너뛴다. 완화는 휘발하는 대화 대신 안 휘발하는 곳에 남기는 것.

**배우는 것**

- 대화에만 있던 제약은 compaction 요약에서 빠질 수 있다 — 루트 CLAUDE.md는 재주입되어 살아남는다
- 완화 5: CLAUDE.md·memory 고정(02·04강) · 수동 `/compact` · `/rewind` 안전지점 · 최소 게이트 1개(14강 Stop 훅) · 결정은 세션 밖(06강 ADR·커밋)
- 새 도구 0 — 앞에서 쌓은 하네스를 위기 상황에 다시 불러 쓴다

**이 브랜치에 들어온 것**

- `HOTFIX.md` — 완화 5종을 절차화한 5줄 카드. 코드·테스트는 `ch3-19-start`(= `ch3-18-done`)와 동일.
- CLAUDE.md엔 이미 가드레일 fail-closed 원칙이 있고(08강), `tests/test_guardrails.py`엔 근거 게이트·출력 유출 fail-closed 테스트가 있다(06·15강) — 19강 최소 게이트가 그대로 성립한다.

**확인해 보기**

```bash
python -m pytest tests/test_guardrails.py -q    # 최소 게이트 — fail-closed 회귀를 잡는다
python -m pytest -q                             # 38 passed
cat HOTFIX.md
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
