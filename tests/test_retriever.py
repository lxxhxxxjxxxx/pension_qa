from app import retriever
from app.retriever import Doc


def test_search_finds_relevant_doc():
    docs = retriever.search("IRP 연금 수령 한도", k=1)
    assert docs and "IRP" in docs[0].name


def test_search_empty_for_unrelated():
    assert retriever.search("점심 메뉴", k=2) == []


def test_search_ranks_tax_credit_doc_for_credit_question():
    docs = retriever.search("연금저축 세액공제 한도", k=1)
    assert docs and "세액공제" in docs[0].name


def test_scores_are_descending():
    hits = retriever.search_scored("연금 수령 과세", k=3)
    assert hits
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


def test_rare_term_outweighs_common_term():
    # '연금'은 모든 문서에 있어 변별력이 없고, 'IRP'는 있는 문서가 적다.
    docs = [
        Doc("공통", "연금 연금 연금 연금 연금 연금 연금 연금"),
        Doc("희귀", "연금 IRP 안내"),
    ]
    hits = retriever.search_scored("연금 IRP", k=2, docs=docs)
    assert hits[0].doc.name == "희귀"


def test_long_doc_does_not_win_by_length_alone():
    # 예전 '토큰 종류 겹침' 방식은 길기만 한 문서가 이겼다.
    padding = " ".join(f"잡담{i}" for i in range(400))
    docs = [
        Doc("짧고정확", "IRP 수령 한도 안내"),
        Doc("길고산만", f"IRP {padding} 한도 {padding} 수령"),
    ]
    hits = retriever.search_scored("IRP 수령 한도", k=2, docs=docs)
    assert hits[0].doc.name == "짧고정확"


def test_repeated_query_term_does_not_inflate_score():
    docs = [Doc("문서", "연금 수령 한도 안내")]
    once = retriever.search_scored("한도", k=1, docs=docs)
    thrice = retriever.search_scored("한도 한도 한도", k=1, docs=docs)
    assert once[0].score == thrice[0].score


def test_min_score_filters_weak_matches():
    docs = [Doc("문서", "연금 수령 한도 안내")]
    assert retriever.search("연금", k=1, docs=docs, min_score=99.0) == []


def test_empty_query_returns_nothing():
    assert retriever.search("!!!", k=2) == []
