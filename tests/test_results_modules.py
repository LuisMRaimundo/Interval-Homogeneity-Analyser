"""
Characterization tests for ``iav.results`` and ``iav.results_aggregate_data``.

Audit summary (no production edits):
- **Active** Streamlit/UI-facing presentation + export modules (not dead code).
- ``interval_analyzer_ui.py`` imports ``render_aggregate_results`` from ``iav.results``.
- ``iav.results`` delegates row/CSV construction to ``iav.results_aggregate_data`` (pure helpers).
- Batch/CLI paths use ``iav.batch_analyze`` JSON/CSV export — parallel, not duplicated here.
- ``results_aggregate_data`` has no Streamlit dependency; ``results`` is Streamlit orchestration only.
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Tuple

import pytest

from iav.analysis_enums import (
    AnalysisThresholdMode,
    HomogeneityMethod,
    HomogeneityScoreKind,
    IntervallicHeadlineMode,
    MusicXmlImportMode,
    VerticalitySliceMode,
)
from iav.interval_analysis_core import metrics_for_notes, set_class_summary_12tet
from iav.results import render_aggregate_results
from iav.results_aggregate_data import (
    adjacency_rows,
    analysis_csv_string,
    interval_label_rows,
    semi_distance_rows,
    write_analysis_csv,
)
from iav.symbolic_profile import intervallic_profile_for_notes
from iav.widget_state import WidgetState

NoteTuple = Tuple[str, float, int]
MAJOR_TRIAD: List[NoteTuple] = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]


def _widget_state(**overrides: Any) -> WidgetState:
    defaults: Dict[str, Any] = {
        "data": [],
        "uploaded": None,
        "xml_mode": MusicXmlImportMode.AGGREGATE,
        "min_slice_notes": 2,
        "include_grace_notes": False,
        "include_cue_notes": False,
        "slice_mode": VerticalitySliceMode.SINGLE,
        "remove_duplicates": False,
        "edo": 12,
        "bin_cents": 100,
        "mode": AnalysisThresholdMode.STANDARD,
        "dominance_threshold": 0.35,
        "even_high": 0.8,
        "even_low": 0.3,
        "chain_threshold": 0.60,
        "homogeneity_method": HomogeneityMethod.DOMINANCE,
        "score_label": HomogeneityScoreKind.DOMINANCE,
        "intervallic_headline_mode": IntervallicHeadlineMode.PAIRWISE,
        "alpha_base": 0.6,
        "auto_alpha": False,
        "k_auto": 4,
        "merge_manual": False,
        "apply_sounding_transpose": False,
    }
    defaults.update(overrides)
    return WidgetState(**defaults)


def _major_triad_metrics(method: str = "dominance"):
    metrics = metrics_for_notes(
        MAJOR_TRIAD,
        0.35,
        0.8,
        0.3,
        0.6,
        method,
        bin_cents=100,
    )
    return metrics


@pytest.fixture
def stub_results_streamlit(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Expander:
        def __enter__(self) -> "_Expander":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr("iav.results.st.subheader", lambda *_a, **_k: None)
    monkeypatch.setattr("iav.results.st.write", lambda *_a, **_k: None)
    monkeypatch.setattr("iav.results.st.caption", lambda *_a, **_k: None)
    monkeypatch.setattr("iav.results.st.expander", lambda *_a, **_k: _Expander())
    monkeypatch.setattr("iav.results.st.slider", lambda *_a, **k: k.get("value", 0.5))
    monkeypatch.setattr("iav.results.st.info", lambda *_a, **_k: None)
    monkeypatch.setattr("iav.results.st.dataframe", lambda *_a, **_k: None)
    monkeypatch.setattr("iav.results.st.download_button", lambda *_a, **_k: None)
    monkeypatch.setattr("iav.results.st.markdown", lambda *_a, **_k: None)
    monkeypatch.setattr("iav.results.render_visualization_section", lambda **_k: None)


def test_semi_distance_rows_empty_counts():
    rows = semi_distance_rows({}, total_intervals=1, bin_cents=100)
    assert rows == []


def test_semi_distance_rows_shape_and_percent():
    rows = semi_distance_rows({4: 2, 7: 1}, total_intervals=3, bin_cents=100)
    assert len(rows) == 2
    assert rows[0] == {
        "Cents": 400,
        "Label": rows[0]["Label"],
        "Count": 2,
        "Percent": pytest.approx(66.67, abs=0.01),
    }
    assert rows[1]["Cents"] == 700
    assert rows[1]["Count"] == 1
    assert rows[1]["Percent"] == pytest.approx(33.33, abs=0.01)


def test_adjacency_rows_single_note_denominator_is_one():
    rows = adjacency_rows({4: 1}, note_count=1, bin_cents=100)
    assert len(rows) == 1
    assert rows[0]["Percent"] == pytest.approx(100.0)


def test_interval_label_rows_sorts_by_count_descending():
    rows = interval_label_rows({"m3": 1, "P5": 3, "M3": 2}, total_intervals=6)
    labels = [r["Interval"] for r in rows]
    assert labels == ["P5", "M3", "m3"]
    assert rows[0]["Percent"] == pytest.approx(50.0)


def test_interval_label_rows_empty_counts():
    rows = interval_label_rows({}, total_intervals=1)
    assert rows == []


def _csv_metric_value(csv_text: str, metric_name: str) -> str:
    reader = csv.reader(io.StringIO(csv_text))
    for row in reader:
        if len(row) >= 2 and row[0] == metric_name:
            return row[1]
    raise AssertionError(f"Metric {metric_name!r} not found in CSV")


def test_analysis_csv_string_dominance_includes_core_metrics():
    metrics = _major_triad_metrics("dominance")
    w = _widget_state()
    semi = semi_distance_rows(metrics["distance_counts"], metrics["total_intervals"], w.bin_cents)
    adj = adjacency_rows(metrics["adj_counts"], len(MAJOR_TRIAD), w.bin_cents)
    interval = interval_label_rows(metrics["interval_counts"], metrics["total_intervals"])
    csv_text = analysis_csv_string(
        w,
        len(MAJOR_TRIAD),
        metrics["total_intervals"],
        metrics,
        0.6,
        float(metrics["H"]),
        semi,
        adj,
        interval,
        None,
    )
    assert _csv_metric_value(csv_text, "Total notes") == "3"
    assert _csv_metric_value(csv_text, "Total pairwise intervals") == str(metrics["total_intervals"])
    assert float(_csv_metric_value(csv_text, metrics["H_primary_title"])) == pytest.approx(
        float(metrics["H"]), abs=1e-6
    )
    assert "Pairwise cents,Label,Count,Percent" in csv_text.replace("\r\n", "\n")
    assert metrics["classification"] in csv_text


def test_analysis_csv_string_combined_mode_includes_consensus_fields():
    metrics = _major_triad_metrics("combined")
    w = _widget_state(homogeneity_method=HomogeneityMethod.COMBINED)
    semi = semi_distance_rows(metrics["distance_counts"], metrics["total_intervals"], w.bin_cents)
    adj = adjacency_rows(metrics["adj_counts"], len(MAJOR_TRIAD), w.bin_cents)
    interval = interval_label_rows(metrics["interval_counts"], metrics["total_intervals"])
    csv_text = analysis_csv_string(
        w,
        len(MAJOR_TRIAD),
        metrics["total_intervals"],
        metrics,
        0.6,
        float(metrics["H_consensus"]),
        semi,
        adj,
        interval,
        None,
    )
    assert float(_csv_metric_value(csv_text, "Homogeneity (consensus)")) == pytest.approx(
        float(metrics["H_consensus"]), abs=1e-6
    )
    assert float(_csv_metric_value(csv_text, "Chain dominance")) == pytest.approx(
        float(metrics["chain_dom"]), abs=1e-6
    )


def test_analysis_csv_string_includes_pc_set_when_provided():
    metrics = _major_triad_metrics()
    w = _widget_state(edo=12)
    pc = set_class_summary_12tet(MAJOR_TRIAD)
    assert pc is not None
    semi = semi_distance_rows(metrics["distance_counts"], metrics["total_intervals"], w.bin_cents)
    adj = adjacency_rows(metrics["adj_counts"], len(MAJOR_TRIAD), w.bin_cents)
    interval = interval_label_rows(metrics["interval_counts"], metrics["total_intervals"])
    csv_text = analysis_csv_string(
        w,
        len(MAJOR_TRIAD),
        metrics["total_intervals"],
        metrics,
        0.6,
        float(metrics["H"]),
        semi,
        adj,
        interval,
        pc,
    )
    assert _csv_metric_value(csv_text, "Prime form (12-TET)") == pc["prime_form_str"]
    assert _csv_metric_value(csv_text, "Interval vector ic1–ic6") == pc["interval_vector_str"]


def test_write_analysis_csv_preserves_row_tables():
    metrics = _major_triad_metrics()
    w = _widget_state()
    semi = semi_distance_rows(metrics["distance_counts"], metrics["total_intervals"], w.bin_cents)
    adj = adjacency_rows(metrics["adj_counts"], len(MAJOR_TRIAD), w.bin_cents)
    interval = interval_label_rows(metrics["interval_counts"], metrics["total_intervals"])
    buf = io.StringIO()
    writer = csv.writer(buf)
    write_analysis_csv(
        writer,
        w,
        len(MAJOR_TRIAD),
        metrics["total_intervals"],
        metrics,
        0.6,
        float(metrics["H"]),
        semi,
        adj,
        interval,
        None,
    )
    rows = list(csv.reader(io.StringIO(buf.getvalue())))
    pairwise_header_idx = next(i for i, r in enumerate(rows) if r[:1] == ["Pairwise cents"])
    assert rows[pairwise_header_idx + 1][0] == str(semi[0]["Cents"])
    label_header_idx = next(
        i for i, r in enumerate(rows) if r[:1] == ["Pairwise interval label"]
    )
    assert rows[label_header_idx + 1][0] == interval[0]["Interval"]


def test_render_aggregate_results_smoke(stub_results_streamlit):
    metrics = _major_triad_metrics()
    w = _widget_state()
    render_aggregate_results(
        w,
        MAJOR_TRIAD,
        metrics,
        0.6,
        deduplication_active=False,
    )


def test_render_aggregate_results_with_intervallic_profile(stub_results_streamlit):
    metrics = _major_triad_metrics()
    profile = intervallic_profile_for_notes(
        MAJOR_TRIAD,
        edo=12,
        distance_counts=metrics["distance_counts"],
    )
    w = _widget_state(edo=12, mode=AnalysisThresholdMode.FIXED_HEURISTIC)
    render_aggregate_results(
        w,
        MAJOR_TRIAD,
        metrics,
        0.6,
        intervallic_profile=profile,
        deduplication_active=True,
    )
