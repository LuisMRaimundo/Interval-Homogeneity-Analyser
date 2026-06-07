"""Focused characterization tests for ``iav.charts`` branches and Streamlit wiring."""

from __future__ import annotations

import sys
import types
from typing import Any, List

import altair as alt
import pandas as pd
import pytest

pytest.importorskip("altair")
pytest.importorskip("pandas")

from iav.charts import (
    chart_adjacent_chain,
    chart_homogeneity_over_time,
    chart_pairwise_by_cents,
    chart_pairwise_by_label,
    chart_pitch_register,
    chart_vertical_cardinality_over_time,
    homogeneity_timeline_dataframe,
    parse_slice_time_quarters,
    render_visualization_section,
    vertical_cardinality_timeline_dataframe,
)


def _is_altair_chart(chart: object) -> bool:
    return hasattr(chart, "to_dict") and callable(chart.to_dict)


def _mark_text(chart: object) -> str | None:
    spec = chart.to_dict()
    mark = spec.get("mark")
    if isinstance(mark, dict):
        return mark.get("text")
    return None


def _has_layer_with_mark(chart: alt.Chart, mark_type: str) -> bool:
    spec = chart.to_dict()
    layers = spec.get("layer", [])
    if not layers and spec.get("mark", {}).get("type") == mark_type:
        return True
    return any(layer.get("mark", {}).get("type") == mark_type for layer in layers)


class _FakeStreamlit:
    def __init__(self) -> None:
        self.altair_charts: List[alt.Chart] = []
        self.captions: List[str] = []
        self.markdowns: List[str] = []

    class _Ctx:
        def __enter__(self) -> "_FakeStreamlit._Ctx":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    def expander(self, *_args: object, **_kwargs: object) -> _Ctx:
        return self._Ctx()

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def columns(self, _n: int) -> List[_Ctx]:
        return [self._Ctx(), self._Ctx()]

    def altair_chart(self, chart: alt.Chart, **_kwargs: object) -> None:
        self.altair_charts.append(chart)

    def markdown(self, text: str) -> None:
        self.markdowns.append(text)


@pytest.fixture
def fake_streamlit(monkeypatch: pytest.MonkeyPatch) -> _FakeStreamlit:
    st = _FakeStreamlit()
    mod = types.ModuleType("streamlit")
    mod.expander = st.expander
    mod.caption = st.caption
    mod.columns = st.columns
    mod.altair_chart = st.altair_chart
    mod.markdown = st.markdown
    monkeypatch.setitem(sys.modules, "streamlit", mod)
    return st


@pytest.mark.parametrize(
    "builder",
    [chart_pairwise_by_label, chart_pairwise_by_cents, chart_adjacent_chain],
)
def test_empty_interval_charts_return_no_data_fallback(builder):
    chart = builder([])
    assert isinstance(chart, alt.Chart)
    assert _mark_text(chart) == "No data"


def test_chart_pitch_register_no_notes_fallback():
    chart = chart_pitch_register([], bin_cents=100)
    assert isinstance(chart, alt.Chart)
    assert chart.to_dict().get("title") == "No notes"


def test_chart_pitch_register_text_label_branch():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    chart = chart_pitch_register(notes, bin_cents=100)
    assert _is_altair_chart(chart)
    assert "layer" in chart.to_dict()
    assert _has_layer_with_mark(chart, "text")


def test_chart_pitch_register_point_only_branch():
    notes = [("C", 0.0, 3 + i) for i in range(25)]
    chart = chart_pitch_register(notes, bin_cents=100)
    assert _is_altair_chart(chart)
    spec = chart.to_dict()
    assert "layer" not in spec
    assert spec["mark"]["type"] == "circle"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (2, 2.0),
        (1.25, 1.25),
        ("1.250", 1.25),
        ("1.0-2.5", 1.75),
    ],
)
def test_parse_slice_time_quarters_valid_inputs(value, expected):
    assert parse_slice_time_quarters(value) == pytest.approx(expected)


def test_parse_slice_time_quarters_invalid_string_raises():
    with pytest.raises(ValueError):
        parse_slice_time_quarters("not-a-time")


def test_homogeneity_timeline_dataframe_empty():
    df = homogeneity_timeline_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_homogeneity_timeline_dataframe_missing_headline_column():
    rows = [{"Slice": 1, "Time (quarters)": 0.0, "Notes": 3}]
    df = homogeneity_timeline_dataframe(rows)
    assert df.empty


def test_homogeneity_timeline_dataframe_skips_invalid_rows():
    rows = [
        {"Slice": 1, "Time (quarters)": "bad", "H (interval dominance)": 0.4, "Notes": 3},
        {"Slice": 2, "Time (quarters)": 1.0, "H (interval dominance)": "n/a", "Notes": 4},
        {
            "Slice": 3,
            "Time": "2.000",
            "Time (quarters)": 2.0,
            "H (interval dominance)": 0.55,
            "Notes": 5,
            "H label": "moderate",
        },
    ]
    df = homogeneity_timeline_dataframe(rows)
    assert len(df) == 1
    assert df.iloc[0]["Slice"] == 3
    assert df.iloc[0]["Time (quarters)"] == pytest.approx(2.0)
    assert df.iloc[0]["H"] == pytest.approx(0.55)
    assert df.iloc[0]["H label"] == "moderate"


def test_vertical_cardinality_timeline_dataframe_empty():
    df = vertical_cardinality_timeline_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_vertical_cardinality_timeline_dataframe_skips_invalid_rows():
    rows = [
        {"Slice": 1, "Time (quarters)": "bad", "Notes": 3},
        {"Slice": 2, "Time (quarters)": 1.0, "Notes": ""},
        {"Slice": 3, "Time (quarters)": 2.0, "Notes": None},
        {"Slice": 4, "Time (quarters)": 3.0, "Notes": "many"},
        {
            "Slice": 5,
            "Time": "4.0-5.0",
            "Time (quarters)": 4.5,
            "Notes": 6,
            "Unique pitches": 4,
            "PC cardinality": 3,
        },
    ]
    df = vertical_cardinality_timeline_dataframe(rows)
    assert len(df) == 1
    assert df.iloc[0]["Slice"] == 5
    assert df.iloc[0]["Time (quarters)"] == pytest.approx(4.5)
    assert df.iloc[0]["vertical_note_count"] == 6
    assert df.iloc[0]["Unique pitches"] == 4


def test_chart_vertical_cardinality_timeline_no_data_fallback():
    chart = chart_vertical_cardinality_over_time(
        [{"Slice": 1, "Time (quarters)": "bad", "Notes": 2}]
    )
    assert isinstance(chart, alt.Chart)
    assert _mark_text(chart) == "No timeline data"


def test_chart_homogeneity_timeline_no_data_fallback():
    chart = chart_homogeneity_over_time([{"Slice": 1, "Time (quarters)": 0.0, "Notes": 2}])
    assert isinstance(chart, alt.Chart)
    assert _mark_text(chart) == "No timeline data"


def test_chart_homogeneity_timeline_single_row_branch():
    rows = [
        {
            "Slice": 1,
            "Time (quarters)": 0.0,
            "H (interval dominance)": 0.42,
            "Notes": 3,
        }
    ]
    chart = chart_homogeneity_over_time(rows)
    assert isinstance(chart, alt.Chart)
    assert _mark_text(chart) == "Need at least 2 slices for a timeline"


def test_render_visualization_section_core_charts(fake_streamlit):
    render_visualization_section(
        interval_rows=[{"Interval": "M3", "Count": 1, "Percent": 100.0}],
        semi_rows=[{"Cents": 400, "Label": "M3", "Count": 1, "Percent": 100.0}],
        adj_rows=[{"Cents": 400, "Label": "M3", "Count": 1, "Percent": 100.0}],
        notes=[("C", 0.0, 4), ("E", 0.0, 4)],
        bin_cents=100,
        edo=24,
        pc_set_summary=None,
    )
    assert len(fake_streamlit.altair_charts) == 4
    assert fake_streamlit.captions
    assert not fake_streamlit.markdowns


def test_render_visualization_section_renders_pitch_class_charts_when_12tet(
    fake_streamlit,
):
    render_visualization_section(
        interval_rows=[],
        semi_rows=[],
        adj_rows=[],
        notes=[("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)],
        bin_cents=100,
        edo=12,
        pc_set_summary={
            "interval_vector": [0, 0, 1, 0, 1, 0],
            "pitch_classes_sorted": [0, 4, 7],
        },
    )
    assert len(fake_streamlit.altair_charts) == 6
    assert any("12-TET pitch-class set" in m for m in fake_streamlit.markdowns)


def test_render_visualization_section_skips_pitch_class_charts_without_summary(
    fake_streamlit,
):
    render_visualization_section(
        interval_rows=[],
        semi_rows=[],
        adj_rows=[],
        notes=[("C", 0.0, 4)],
        bin_cents=100,
        edo=12,
        pc_set_summary=None,
    )
    assert len(fake_streamlit.altair_charts) == 4
    assert not fake_streamlit.markdowns
