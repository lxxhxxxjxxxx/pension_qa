프로젝트 개요는 @README.md 를 참고. 사용 가능한 명령은 README의 실행 섹션과 동일.

# pension_qa — 연금 안내 RAG 에이전트

## 명령
- 설치: `pip install -r requirements.txt`
- 실행: `python -m app.main "질문"`
- 테스트: `python -m pytest -q`

## 도메인
- 이 프로젝트는 연금(연금저축·IRP) 질문에 `data/`의 가상 연금 가이드를 검색(RAG)해 근거와 함께 답하는 에이전트다.
- 모든 세율·한도는 가상 예시다(실제 세법·법령 아님).
- 챗봇의 답변 행동 규칙(근거 범위 내 답변·모르면 모른다고)은 이 파일이 아니라 `app/llm.py`의 SYSTEM 프롬프트가 정본.

## 컨벤션
- Python 3.11+, 표준 라이브러리 우선, 의존성 최소.
- 가드레일 로직은 `app/guardrails.py` 한 곳에만 둔다(입력 PII·범위 / 출력 유출).
- 응답 경로 코드는 반드시 근거 문서(`Result.sources`)를 채운다 — 답변만 반환하는 코드 금지.
- 테스트는 소스 옆 `tests/`에, 함수 단위로.
- 가드레일은 fail-closed를 유지한다 — PII 체크에 예외를 뚫을 땐 `tests/test_guardrails.py`를 먼저 고친다.

## 금지
- 실제 개인정보(주민번호·계좌)를 코드·테스트 데이터·로그 출력에 넣지 말 것.
- `data/` 문서·코드의 세율·한도를 실제 법령 수치로 "바로잡지" 말 것 — 전부 의도된 가상 예시다.
- 금액 계산에 float를 쓰지 말 것 — 반드시 `Decimal`(`app/pension_calc.py`가 기준).
- 가드레일을 우회하거나 약화시키지 말 것.
