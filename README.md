> 📚 **강의 스냅샷 — 17강을 마친 상태입니다.**  
> 시작점 `ch3-17-start` → **지금 여기 `ch3-17-done`** → 다음 강 시작점 `ch3-18-start`

## 17강 · [안티패턴] 통합 단계 진단 + 샌드박스·MCP 진입

Part 2 시작. 외부를 붙이는 순간 생기는 문제 다섯(스코프·비용·에러·시크릿·인젝션)을 짚고, 첫 안전장치로 샌드박스(OS 격리)를 켠다. 전제는 "외부는 못 믿는다".

**배우는 것**

- 한 줄 요청("평가액 API를 MCP로 붙여줘")엔 다섯 항목이 없다 — 채워지는 건 하네스가 정해 둔 만큼
- 권한·모드·샌드박스 세 층 — permissions는 판단 위, 샌드박스는 판단 아래(OS)
- 샌드박스는 Bash만 격리한다 — MCP 서버·hooks는 호스트에서 돈다(→ 18강)

**이 브랜치에 들어온 것**

- 없음(레포 무변경). 샌드박스 설정은 gitignore되는 `.claude/settings.local.json`에만 쓴다. 코드는 `ch3-17-start`(= `ch2-16-done`)와 동일.

**확인해 보기**

```bash
python -m pytest -q        # 38 passed
claude                     # /sandbox → Mode·Overrides·Config 세 탭 (Linux/WSL은 bubblewrap·socat 필요)
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
