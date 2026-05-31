"""Smoke tests for chart builders (no Streamlit; requires altair + pandas)."""

import pytest

pytest.importorskip("altair")
pytest.importorskip("pandas")

from iav.charts import (
    chart_adjacent_chain,
    chart_homogeneity_over_time,
    chart_interval_vector_bars,
    chart_pairwise_by_cents,
    chart_pairwise_by_label,
    chart_pitch_class_presence,
    chart_pitch_register,
    chart_vertical_cardinality_over_time,
    homogeneity_timeline_dataframe,
    vertical_cardinality_timeline_dataframe,
)


def test_adjacent_and_cents_charts():
    rows = [{"Cents": 100, "Label": "m2", "Count": 1, "Percent": 33.0}]
    assert chart_adjacent_chain(rows) is not None
    assert chart_pairwise_by_cents(rows) is not None


def test_pairwise_label_chart():
    c = chart_pairwise_by_label([{"Interval": "M2", "Count": 2, "Percent": 40.0}])
    assert c is not None


def test_pitch_register():
    notes = [("C", 0.0, 4), ("G", 0.0, 4)]
    c = chart_pitch_register(notes, bin_cents=100)
    assert c is not None


def test_iv_bars():
    c = chart_interval_vector_bars([0, 0, 1, 0, 1, 0])
    assert c is not None


def test_homogeneity_timeline_chart():
    rows = [
        {"Slice": 1, "Time": "0.000", "Time (quarters)": 0.0, "H (interval dominance)": 0.4, "Notes": 4},
        {"Slice": 2, "Time": "1.000", "Time (quarters)": 1.0, "H (interval dominance)": 0.7, "Notes": 5},
        {"Slice": 3, "Time": "2.000-3.000", "Time (quarters)": 2.0, "H (interval dominance)": 0.5, "Notes": 6},
    ]
    df = homogeneity_timeline_dataframe(rows)
    assert len(df) == 3
    assert chart_homogeneity_over_time(rows) is not None


def test_vertical_cardinality_timeline_chart():
    rows = [
        {"Slice": 1, "Time (quarters)": 0.0, "Notes": 3},
        {"Slice": 2, "Time (quarters)": 1.0, "Notes": 4},
    ]
    vdf = vertical_cardinality_timeline_dataframe(rows)
    assert len(vdf) == 2
    assert chart_vertical_cardinality_over_time(rows) is not None


def test_pc_presence():
    c = chart_pitch_class_presence([0, 4, 7])
    assert c is not None
