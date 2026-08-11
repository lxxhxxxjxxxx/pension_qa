from app import retriever
from app.retriever import Doc


def test_search_finds_relevant_doc():
    docs = retriever.search("IRP 연금 수령 한도", k=1)
    assert docs and "IRP" in docs[0].name


def test_search_empty_for_unrelated():
    assert retriever.search("점심 메뉴", k=2) == []


# 점수 — 겹침 개수 세기로는 구분되지 않던 세 가지(BM25 도입 근거)


def _rank(query, docs):
    return [s.doc.name for s in retriever.score_docs(query, docs)]


def test_rare_term_outranks_many_common_terms():
    """희귀 토큰 1개 > 모든 문서에 있는 흔한 토큰 2개. 개수만 세면 반대로 나왔다."""
    docs = [
        Doc("흔한말_뭉치", "연금 문서 연금 문서 안내 자료"),
        Doc("안내", "연금 문서 안내"),
        Doc("요약", "연금 문서 요약"),
        Doc("정리", "연금 문서 정리"),
        Doc("희귀어", "IRP 수령한도"),
    ]
    assert _rank("연금 문서 IRP", docs)[0] == "희귀어"


def test_padding_does_not_win_by_length():
    """같은 토큰을 같은 횟수 언급했다면 짧은 문서가 앞선다(길이 정규화)."""
    docs = [
        Doc("긴문서", "IRP 수령 " + "잡담 " * 40),
        Doc("짧은문서", "IRP 수령 요건 안내"),
    ]
    assert _rank("IRP 수령", docs)[0] == "짧은문서"


def test_repeated_mention_outranks_single_mention():
    """토큰 집합이 같아도 그 주제를 여러 번 다룬 문서가 앞선다(TF)."""
    docs = [
        Doc("한번", "IRP 안내 자료 정리 문서 요약"),
        Doc("여러번", "IRP IRP IRP 안내 자료 정리 문서 요약"),
    ]
    assert _rank("IRP", docs)[0] == "여러번"


def test_score_zero_docs_are_dropped():
    docs = [Doc("무관", "점심 메뉴 추천"), Doc("관련", "IRP 수령 요건")]
    assert [d.name for d in retriever.search("IRP", k=2, docs=docs)] == ["관련"]


def test_ranking_is_deterministic_on_ties():
    """동점이면 이름순 — 파일 나열 순서에 따라 결과가 흔들리지 않게."""
    docs = [Doc("나", "IRP 수령"), Doc("가", "IRP 수령")]
    assert _rank("IRP 수령", docs) == ["가", "나"]
