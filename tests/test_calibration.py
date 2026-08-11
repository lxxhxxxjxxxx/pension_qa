"""커버리지 캘리브레이션 회귀 — ADR 0002 임계값이 여전히 유효한지 고정한다.

`guardrails.HARD_THRESHOLD`/`SOFT_THRESHOLD`는 현재 `data/` 3개 문서의 실측 분포로 잡혀 있다.
검색기를 바꾸거나 문서를 늘리면 이 표가 먼저 깨지고, 그때가 재캘리브레이션 시점이다.

측정값은 BM25 도입(랭킹 점수 개선) 전후가 동일하다 — 랭킹만 바꾸고 커버리지 정의는
건드리지 않았기 때문. SPEC_score.md 표의 잡담 질문은 0.07로 적혀 있으나 실측은 0.125다
(BM25 도입 전에도 0.125였다). 구간 판정은 같아 임계값에는 영향이 없다.
"""
import pytest

from app import guardrails, retriever

# (질문, 커버리지, 기대 구간)
CALIBRATION = [
    ("퇴직금 받았는데 IRP로 옮기면 세금 어떻게 되나요?", 0.0, guardrails.EVIDENCE_BLOCK),
    ("연금저축 관련해서 요즘 날씨랑 점심 메뉴 뭐가 좋을까요", 0.125, guardrails.EVIDENCE_BLOCK),
    ("연금 해지하면 어떻게 되나요", 0.25, guardrails.EVIDENCE_LOW),
    ("연금저축 세액공제 한도가 얼마인가요?", 0.5, guardrails.EVIDENCE_OK),
    ("연금소득세 과세 어떻게 되나요", 0.5, guardrails.EVIDENCE_OK),
    ("IRP 수령 요건 알려줘", 0.75, guardrails.EVIDENCE_OK),
]


@pytest.mark.parametrize("question,coverage,level", CALIBRATION)
def test_coverage_bands_unchanged(question, coverage, level):
    found = retriever.search_scored(question)
    assert found.coverage == pytest.approx(coverage, abs=0.005)
    assert guardrails.check_evidence(found.coverage).level == level
