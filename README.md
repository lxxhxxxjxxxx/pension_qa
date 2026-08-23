> 📚 **강의 스냅샷 — 02강을 마친 상태입니다.**  
> 시작점 `ch1-02-start` → **지금 여기 `ch1-02-done`** → 다음 강 시작점 `ch1-03-start`

## 02강 · 주입 컨텍스트로서의 CLAUDE.md

빈 `.claude/`에 CLAUDE.md를 깔아 "개인 비서"를 "팀 공유 컨텍스트"로 바꾼다.

**배우는 것**

- `/init`으로 초안을 뽑고 **손으로** 4덩어리(명령·도메인·컨벤션·금지)를 채운다
- 어디에 두나 — 4스코프와 로드 순서. `/memory`에 안 보이면 Claude가 못 보는 것(디버깅 1순위)
- CLAUDE.md는 **유도**지 강제가 아니다 → 05강 permissions · 14강 Hooks로 이어진다

**이 브랜치에 들어온 것**

- `CLAUDE.md` — 명령 · 도메인 · 컨벤션 · 금지

**확인해 보기**

```bash
git diff ch1-02-start..ch1-02-done --stat
python -m pytest -q        # 11 passed
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
