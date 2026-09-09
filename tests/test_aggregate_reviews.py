"""26강 — 집계 규칙이 결정적임을 잠근다(같은 입력 → 같은 판정, 모델 무관).

리뷰어 발견은 확률적(모델 턴)이지만, 여기 규칙은 고정 입력을 받아 순수 함수로 판정한다.
그래서 테스트가 성립한다 — 리뷰 자체가 아니라 '집계'를 검증한다.
"""

from scripts.aggregate_reviews import aggregate


def test_two_votes_confirm():
    # 규칙1: 같은 file:line을 서로 다른 두 리뷰어가 독립 지적 → confirm
    findings = [
        {"reviewer": "accuracy", "severity": "Important", "file": "app/guardrails.py", "line": 42, "note": ""},
        {"reviewer": "security", "severity": "Important", "file": "app/guardrails.py", "line": 42, "note": ""},
    ]
    rows, gate = aggregate(findings, [])
    assert len(rows) == 1
    assert rows[0]["decision"] == "confirm"
    assert rows[0]["rule"].startswith("규칙1")
    assert gate == 1  # confirm된 Important 1건 → 게이트 차단


def test_line_tolerance_merges_votes():
    # 42/43은 같은 발견으로 묶여야 2표가 된다(±LINE_TOL). 안 묶으면 규칙1이 무너진다.
    findings = [
        {"reviewer": "accuracy", "severity": "Important", "file": "a.py", "line": 42, "note": ""},
        {"reviewer": "perf", "severity": "Important", "file": "a.py", "line": 43, "note": ""},
    ]
    rows, _ = aggregate(findings, [])
    assert len(rows) == 1
    assert rows[0]["votes"] == 2


def test_one_vote_with_machine_evidence_confirm():
    # 규칙2: 1표라도 적대적 검증을 '기계 증거'(grep/test)로 통과 → confirm
    findings = [{"reviewer": "security", "severity": "Important", "file": "log.py", "line": 88, "note": ""}]
    verdicts = [{"file": "log.py", "line": 88, "verdict": "survived", "evidence": "grep", "detail": ""}]
    rows, gate = aggregate(findings, verdicts)
    assert rows[0]["decision"] == "confirm"
    assert rows[0]["rule"].startswith("규칙2")
    assert gate == 1


def test_one_vote_refuted_dropped():
    # 규칙3: 1표 + 적대적 검증 논파(FP) → 폐기
    findings = [{"reviewer": "perf", "severity": "Important", "file": "app/retriever.py", "line": 15, "note": ""}]
    verdicts = [{"file": "app/retriever.py", "line": 15, "verdict": "refuted", "evidence": None, "detail": ""}]
    rows, gate = aggregate(findings, verdicts)
    assert rows[0]["decision"] == "폐기"
    assert rows[0]["rule"].startswith("규칙3")
    assert gate == 0  # 폐기됐으니 게이트 통과


def test_one_vote_no_evidence_dropped():
    # 규칙3: 1표 + 검증 자체가 없음 → 폐기(확인 안 된 단독 지적은 통과 못 시킨다)
    findings = [{"reviewer": "perf", "severity": "Important", "file": "app/retriever.py", "line": 33, "note": ""}]
    rows, gate = aggregate(findings, [])
    assert rows[0]["decision"] == "폐기"
    assert gate == 0


def test_two_votes_but_refuted_dropped():
    # 논파는 표수를 이긴다: 2표라도 적대적 검증이 FP로 뒤집으면 폐기(다수결 함정 방지).
    findings = [
        {"reviewer": "accuracy", "severity": "Important", "file": "b.py", "line": 10, "note": ""},
        {"reviewer": "perf", "severity": "Important", "file": "b.py", "line": 10, "note": ""},
    ]
    verdicts = [{"file": "b.py", "line": 10, "verdict": "refuted", "evidence": None, "detail": ""}]
    rows, gate = aggregate(findings, verdicts)
    assert rows[0]["decision"] == "폐기"
    assert gate == 0


def test_deterministic_same_input_same_output():
    # 같은 입력을 뒤섞어 두 번 돌려도 판정이 같다(집계는 순서·실행에 안 흔들린다).
    findings = [
        {"reviewer": "security", "severity": "Important", "file": "app/guardrails.py", "line": 42, "note": ""},
        {"reviewer": "accuracy", "severity": "Important", "file": "app/guardrails.py", "line": 42, "note": ""},
        {"reviewer": "perf", "severity": "Nit", "file": "app/retriever.py", "line": 33, "note": ""},
    ]
    r1, g1 = aggregate(findings, [])
    r2, g2 = aggregate(list(reversed(findings)), [])
    assert g1 == g2
    assert [(r["file"], r["line"], r["decision"]) for r in r1] == [
        (r["file"], r["line"], r["decision"]) for r in r2
    ]


def test_nit_never_blocks_gate():
    # 게이트는 confirm된 🔴 Important만 센다 — Nit은 아무리 confirm돼도 머지를 막지 않는다.
    findings = [
        {"reviewer": "accuracy", "severity": "Nit", "file": "c.py", "line": 5, "note": ""},
        {"reviewer": "perf", "severity": "Nit", "file": "c.py", "line": 5, "note": ""},
    ]
    rows, gate = aggregate(findings, [])
    assert rows[0]["decision"] == "confirm"
    assert gate == 0
