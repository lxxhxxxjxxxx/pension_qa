from app import guardrails, retriever
from app.retriever import Doc


def test_search_finds_relevant_doc():
    docs = retriever.search("IRP 연금 수령 한도", k=1)
    assert docs and "IRP" in docs[0].name


def test_search_empty_for_unrelated():
    assert retriever.search("점심 메뉴", k=2) == []


# BM25 랭킹 — 겹침 개수만 세던 방식이 못 하던 것


def test_rare_term_outranks_ubiquitous_term_at_equal_overlap():
    """겹친 토큰 수가 같으면, 희소 토큰을 맞춘 문서가 이겨야 한다(IDF)."""
    docs = [
        Doc("common", "연금 자료"),  # 겹침 1개 — 단 '연금'은 모든 문서에 있음
        Doc("rare", "세액공제 자료"),  # 겹침 1개 — '세액공제'는 여기에만
        Doc("filler_a", "연금 기타"),
        Doc("filler_b", "연금 참고"),
    ]
    top = retriever.search("연금 세액공제", k=1, docs=docs)
    assert [d.name for d in top] == ["rare"]


def test_short_focused_doc_outranks_padded_long_doc():
    """같은 토큰을 같은 횟수로 맞췄다면 분량이 적은 쪽이 이겨야 한다(길이 정규화)."""
    docs = [
        Doc("padded", "연금 수령 요건 " + "기타 " * 100),
        Doc("focused", "연금 수령 요건"),
    ]
    top = retriever.search("연금 수령 요건", k=1, docs=docs)
    assert [d.name for d in top] == ["focused"]


def test_zero_overlap_still_excluded():
    """BM25로 바꿔도 `score > 0`은 여전히 '질문 토큰이 최소 하나 등장'을 뜻한다."""
    docs = [Doc("unrelated", "점심 메뉴 안내")]
    assert retriever.search("연금 수령", k=2, docs=docs) == []


def test_empty_query_returns_nothing():
    assert retriever.search_scored("!!!").docs == []
    assert retriever.search_scored("!!!").coverage == 0.0


# ADR 0002 캘리브레이션 — 검색기를 바꾸면 여기서 먼저 깨져야 한다.
# 임계값(0.15/0.40)은 현재 data/ 3개 문서 실측 분포로 잡혀 있다.


def _band(question: str) -> str:
    return guardrails.check_evidence(retriever.search_scored(question).coverage).level


def test_adr0002_calibration_bands_hold():
    expected = {
        "퇴직금 받았는데 IRP로 옮기면 세금 어떻게 되나요?": guardrails.EVIDENCE_BLOCK,
        "연금저축 관련해서 요즘 날씨랑 점심 메뉴 뭐가 좋을까요": guardrails.EVIDENCE_BLOCK,
        "연금 해지하면 어떻게 되나요": guardrails.EVIDENCE_LOW,
        "연금저축 세액공제 한도가 얼마인가요?": guardrails.EVIDENCE_OK,
        "연금소득세 과세 어떻게 되나요": guardrails.EVIDENCE_OK,
        "IRP 수령 요건 알려줘": guardrails.EVIDENCE_OK,
    }
    assert {q: _band(q) for q in expected} == expected
