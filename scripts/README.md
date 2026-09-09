# scripts/ — 26강 적대적 리뷰어 집계

`aggregate_reviews.py` — 확률적 리뷰어 N개의 발견을 **결정적 규칙**으로 집계한다(ADR 0011).

## 고정 입력 (촬영 재현용)

리뷰 자체는 모델 턴이라 매번 갈린다. 강의에서 **집계**를 결정적으로 보이려고, 리뷰어·검증 결과를
고정 픽스처로 박아 둔다 — `aggregate_reviews.py`는 이걸 읽어 표·게이트를 산출한다.

- `mock_reviews.jsonl` — 세 리뷰어(accuracy·security·perf)의 발견. 각 줄 `{reviewer, severity, file, line, note}`.
- `mock_verdicts.jsonl` — 1표짜리 발견에 대한 적대적 검증 판정. `{file, line, verdict(survived|refuted), evidence(grep|test|null), detail}`.

가상 PR이 하나 올라온 상황을 가정한다. 좌표 주의:
- `app/guardrails.py:42` · `app/retriever.py:15/33` — **레포에 실재**하는 파일.
- `log.py:88` — **이 가상 PR이 새로 추가한 파일**(레포엔 아직 없음). 그래서 검증은 grep(마스킹 함수 부재)으로 한다.

## 실행

```bash
python3 scripts/aggregate_reviews.py    # 표 + 게이트 출력, confirm된 Important>0이면 exit 1
```

집계 규칙 검증은 `tests/test_aggregate_reviews.py`(8건) — 모델 없이 결정적으로 돈다.
