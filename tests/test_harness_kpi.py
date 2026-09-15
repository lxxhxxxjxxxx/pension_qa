"""29강 — KPI 두 단계. 결과 지표는 지어내지 않는다(기록이 없으면 '미기록')."""
from pathlib import Path

from scripts import harness_kpi as hk
from scripts import otel_log

FIX = Path(__file__).resolve().parent.parent / "scripts" / "mock_otel_console.log"


def test_오탐률은_26강_verdicts_에서_나온다():
    row = next(r for r in hk.outcome_metrics() if r["kpi"] == "오탐률")
    assert row["value"].startswith("1/3")


def test_MTTD_MTTR_은_시각이_없으면_미기록():
    row = next(r for r in hk.outcome_metrics() if r["kpi"] == "MTTD · MTTR")
    assert row["value"] in ("미기록", "근거 없음")


def test_적발률은_집계_confirm_에서_센다():
    row = next(r for r in hk.proxy_metrics(None, prs=1) if r["kpi"] == "적발률")
    assert row["value"].startswith("2건 / 1 PR")


def test_로그가_있으면_작업당_비용이_나온다():
    rows = hk.proxy_metrics(otel_log.load(FIX), prs=1)
    cost = next(r for r in rows if r["kpi"] == "작업당 비용")
    assert cost["value"].startswith("$0.4")
