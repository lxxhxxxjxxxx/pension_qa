from app import retriever


def test_search_finds_relevant_doc():
    docs = retriever.search("IRP 연금 수령 한도", k=1)
    assert docs and "IRP" in docs[0].name


def test_search_empty_for_unrelated():
    assert retriever.search("점심 메뉴", k=2) == []
