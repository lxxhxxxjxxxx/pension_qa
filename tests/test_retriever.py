import pytest

from app import guardrails, retriever


def test_search_finds_relevant_doc():
    docs = retriever.search("IRP 연금 수령 한도", k=1)
    assert docs and "IRP" in docs[0].name


def test_search_empty_for_unrelated():
    assert retriever.search("점심 메뉴", k=2) == []


# 스코어링 규칙 — 합성 문서로 규칙 하나씩 고정한다


def _docs(*pairs: tuple[str, str]) -> list[retriever.Doc]:
    return [retriever.Doc(name, text) for name, text in pairs]


def test_rare_term_outranks_common_term():
    """IDF — 흔한 토큰만 걸린 문서보다 희소 토큰이 걸린 문서가 앞선다."""
    docs = _docs(
        ("흔한말만", "연금 납입"),
        ("희소어걸림", "한도 납입"),
        ("연금뿐1", "연금 과세"),
        ("연금뿐2", "연금 수령"),
    )
    found = retriever.search("연금 한도", k=1, docs=docs)
    assert [d.name for d in found] == ["희소어걸림"]


def test_particle_attached_token_still_matches():
    """조사가 붙은 토큰(`IRP로`)도 근거 문서를 찾는다 — 정확 일치만 보던 시절의 리콜 구멍."""
    found = retriever.search("퇴직금 받았는데 IRP로 옮기면 세금 어떻게 되나요?", k=1)
    assert [d.name for d in found] == ["IRP_수령요건"]


def test_prefix_match_scores_below_exact_match():
    """접두 일치(`연금`~`연금저축`)는 정확 일치보다 낮게 친다."""
    docs = _docs(("정확일치", "연금 안내"), ("접두일치", "연금저축 안내"))
    found = retriever.search_scored("연금", k=2, docs=docs)
    assert [d.name for d in found.docs] == ["정확일치", "접두일치"]

    prefix_only = retriever.search_scored("연금", k=2, docs=_docs(("접두일치", "연금저축 안내")))
    assert [d.name for d in prefix_only.docs] == ["접두일치"]
    assert 0.0 < prefix_only.coverage < 1.0


def test_suffix_only_overlap_scores_nothing():
    """조사(`으로`)가 복합어(`연금으로`) 꼬리에 걸려 점수를 얻으면 안 된다 — 랭킹이 뒤집힌다."""
    docs = _docs(("꼬리만겹침", "연금으로 수령"))
    assert retriever.search("으로", k=2, docs=docs) == []


def test_single_char_token_does_not_partial_match():
    """1글자 토큰은 아무 데나 걸리므로 부분 일치를 인정하지 않는다."""
    assert retriever.search("가", k=2, docs=_docs(("잡음", "가나다 라마바"))) == []


def test_long_doc_does_not_win_on_length_alone():
    """길이 정규화 — 같은 토큰이 걸렸다면 짧은 문서가 앞선다."""
    docs = _docs(
        ("짧은문서", "세액공제 안내"),
        ("긴문서", "세액공제 " + " ".join(f"잡토큰{i}" for i in range(40))),
    )
    found = retriever.search("세액공제", k=2, docs=docs)
    assert [d.name for d in found] == ["짧은문서", "긴문서"]


def test_tie_is_broken_by_name_deterministically():
    docs = _docs(("나문서", "연금 수령"), ("가문서", "연금 수령"))
    found = retriever.search("연금 수령", k=2, docs=docs)
    assert [d.name for d in found] == ["가문서", "나문서"]


# 커버리지 — 근거 게이트(ADR 0002)의 입력


def test_coverage_is_zero_when_nothing_matches():
    assert retriever.search_scored("점심 메뉴").coverage == 0.0


def test_masked_email_does_not_dilute_coverage():
    """입력 마스킹(ADR 0001) 결과가 커버리지 분모를 키워 게이트를 흐리면 안 된다."""
    plain = retriever.search_scored("연금저축 세액공제 한도가 얼마인가요?")
    masked = retriever.search_scored("연금저축 세액공제 한도가 얼마인가요? 회신 h***@e***.com")
    assert [d.name for d in masked.docs] == [d.name for d in plain.docs]
    assert guardrails.check_evidence(masked.coverage).level == guardrails.EVIDENCE_OK


# 임계 캘리브레이션 회귀 — 검색 점수가 바뀌면 ADR 0002 구간이 밀린다.
# 아래 표가 깨지면 검색기든 임계값이든 한쪽을 재캘리브레이션해야 한다는 신호다.
_CALIBRATION = [
    ("퇴직금 받았는데 IRP로 옮기면 세금 어떻게 되나요?", guardrails.EVIDENCE_BLOCK),
    ("연금저축 관련해서 요즘 날씨랑 점심 메뉴 뭐가 좋을까요", guardrails.EVIDENCE_BLOCK),
    ("연금 해지하면 어떻게 되나요", guardrails.EVIDENCE_LOW),
    ("연금저축 세액공제 한도가 얼마인가요?", guardrails.EVIDENCE_OK),
    ("연금소득세 과세 어떻게 되나요", guardrails.EVIDENCE_OK),
    ("IRP 수령 요건 알려줘", guardrails.EVIDENCE_OK),
]


@pytest.mark.parametrize("question,expected", _CALIBRATION)
def test_coverage_stays_in_calibrated_band(question, expected):
    coverage = retriever.search_scored(question).coverage
    assert guardrails.check_evidence(coverage).level == expected, f"{question} → {coverage:.3f}"
