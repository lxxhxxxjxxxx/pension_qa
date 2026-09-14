<!-- 27강 고정 입력 — 리뷰어가 뱉은 리포트(25강 output-style 포맷). 촬영 재현용.

리뷰 turn 자체는 모델이라 매번 갈린다. 그 확률적 산출을 여기 고정해 두고,
백로그 라우팅·병합은 결정적으로 재현한다(26강 mock_reviews.jsonl 과 같은 장치).
좌표는 전부 레포에 실재하는 줄이다 — 에디터로 열어 확인할 수 있다. -->

## 🔴 Important  (머지 전 반드시 수정)
- [app/guardrails.py:42] 출력 유출 체크가 조기 반환으로 우회될 수 있다 — fail-open

## 🟡 Nit  (선택 · 최대 5개)
- [app/retriever.py:33] 변수명 docs 가 모호 — 26강 집계에서도 같은 자리가 나왔다(병합되어 한 줄로 수렴한다)
- [app/retriever.py:35] 상위 k 기본값 2 가 매직넘버 — 모듈 상수로 빼면 의도가 드러난다
- [app/agent.py:34] 변수명 names 가 모호 — source_names 가 읽힌다

## 🟣 Pre-existing  (기존 문제, 이번 PR 책임 아님 — 기록만)
- [app/main.py:9] CLI 진입 경로에 테스트가 없다 — 커버 0%
- [app/retriever.py:49] 문서 토큰을 질의마다 재계산한다 — 캐시 도입 검토

## Summary
Important 1건 · Nit 3건 · Pre-existing 2건 — 유출 우회 하나만 오늘 막고, 나머지는 부채 큐로.
