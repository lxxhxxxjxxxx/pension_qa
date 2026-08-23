# ADR 0003 — 가드레일 입력/출력 분리, fail-closed

## 상태
채택

## 맥락
Ch1에서 CLAUDE.md·rules·settings·agents로 하네스를 쌓았다. 가드레일이 무엇을
어디까지 책임지는지가 규칙 여러 곳에 흩어져 있어, 결정 자체를 한 장으로 남긴다.

## 결정
가드레일은 입력(PII·범위)과 출력(유출)을 분리하고, 판정 애매 시 차단(fail-closed).

## 이유
금융 규제 맥락 — 놓치는 것보다 과차단이 안전.

## 결과
- `.claude/rules/guardrails.md`의 path-scoped 규칙과 `app/guardrails.py`가 같은 기준을 가리킨다.
- 트레이드오프: 과차단으로 정상 질문이 막히는 경우가 생긴다 — 범위 키워드 확대는
  fail-open 방향이므로 ADR 없이 넓히지 않는다.
