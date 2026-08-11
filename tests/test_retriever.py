from app import guardrails, retriever


def test_search_finds_relevant_doc():
    docs = retriever.search("IRP 연금 수령 한도", k=1)
    assert docs and "IRP" in docs[0].name


def test_search_empty_for_unrelated():
    assert retriever.search("점심 메뉴", k=2) == []


# 접사 정규화 — 조사·어미가 붙어도 같은 토큰으로 본다(ADR 0003)


def test_particle_is_stripped_from_query_token():
    docs = [retriever.Doc("한도", "연금 수령 한도 규정"), retriever.Doc("무관", "점심 메뉴 안내")]
    assert [d.name for d in retriever.search("한도가", k=1, docs=docs)] == ["한도"]


def test_particle_is_stripped_from_doc_token():
    docs = [retriever.Doc("납입", "납입액을 합산한다"), retriever.Doc("무관", "점심 메뉴 안내")]
    assert [d.name for d in retriever.search("납입액", k=1, docs=docs)] == ["납입"]


def test_short_token_is_not_over_stripped():
    """`한도`에서 조사 `도`를 떼면 `한`이 된다 — 최소 어간 길이로 막는다."""
    assert retriever._variants("한도") == {"한도"}


def test_verb_ending_is_stripped():
    docs = [retriever.Doc("해지", "중도해지 시 기타소득세"), retriever.Doc("무관", "점심 메뉴 안내")]
    assert [d.name for d in retriever.search("해지하면", k=1, docs=docs)] == ["해지"]


# 복합명사 포함 매칭 — 방향은 질문 → 문서 한쪽만


def test_question_token_matches_inside_doc_compound():
    docs = [retriever.Doc("과세", "종합과세 기준"), retriever.Doc("무관", "점심 메뉴 안내")]
    assert [d.name for d in retriever.search("과세", k=1, docs=docs)] == ["과세"]


def test_doc_token_does_not_cover_more_specific_question_token():
    """문서의 `연금`이 질문의 `연금소득세`를 커버한 것으로 치면 특이 용어의 IDF가 무너진다."""
    docs = [retriever.Doc("일반", "연금 안내"), retriever.Doc("무관", "점심 메뉴 안내")]
    assert retriever.search("연금소득세", k=2, docs=docs) == []


# IDF 가중 커버리지


def test_common_token_covers_less_than_rare_token():
    docs = [
        retriever.Doc("a", "연금 세액공제 안내"),
        retriever.Doc("b", "연금 수령 안내"),
        retriever.Doc("c", "연금 과세 안내"),
    ]
    common = retriever.search_scored("연금", k=2, docs=docs).coverage
    rare = retriever.search_scored("세액공제", k=2, docs=docs).coverage
    assert common < rare


def test_single_common_token_falls_below_hard_threshold():
    """예전 검색기에서 `"연금"` 한 단어는 커버리지 1.00으로 게이트를 그냥 통과했다(ADR 0003)."""
    assert retriever.search_scored("연금").coverage < guardrails.HARD_THRESHOLD


def test_unknown_tokens_do_not_outweigh_rarest_real_term():
    """이메일 한 줄이 붙었다고 근거가 확실한 질문이 보류로 떨어지면 안 된다."""
    base = retriever.search_scored("연금저축 세액공제 한도가 얼마인가요?")
    with_email = retriever.search_scored("연금저축 세액공제 한도가 얼마인가요 문의는 hong@example.com 으로")
    assert with_email.coverage >= guardrails.HARD_THRESHOLD
    assert [d.name for d in with_email.docs] == [d.name for d in base.docs]


def test_empty_query_is_not_a_division_error():
    assert retriever.search_scored("!!!").coverage == 0.0
