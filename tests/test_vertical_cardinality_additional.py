"""Focused characterization tests for ``iav.vertical_cardinality`` edge branches."""

from __future__ import annotations

import json

import pytest

from iav.analysis_enums import MusicXmlImportMode
from iav.vertical_cardinality import (
    DEFINITIONS,
    VERTICAL_CARDINALITY_SCHEMA_VERSION,
    build_vertical_cardinality_profile,
    build_vertical_cardinality_series,
    enrich_slice_summary_row,
    vertical_cardinality_for_notes,
    vertical_cardinality_from_summary_row,
    vertical_cardinality_profile_json,
)

MAJOR_TRIAD = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]


def test_vertical_cardinality_for_notes_empty_12tet():
    card = vertical_cardinality_for_notes([], bin_cents=100, edo=12)
    assert card == {
        "vertical_note_count": 0,
        "vertical_unique_pitch_count": 0,
        "vertical_pitch_class_cardinality": 0,
    }


def test_vertical_cardinality_for_notes_empty_non_12tet():
    card = vertical_cardinality_for_notes([], bin_cents=100, edo=24)
    assert card["vertical_note_count"] == 0
    assert card["vertical_unique_pitch_count"] == 0
    assert card["vertical_pitch_class_cardinality"] is None


def test_vertical_cardinality_for_notes_single_note():
    card = vertical_cardinality_for_notes([("G", 0.0, 3)], bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 1
    assert card["vertical_unique_pitch_count"] == 1
    assert card["vertical_pitch_class_cardinality"] == 1


def test_vertical_cardinality_for_notes_duplicate_events_count_events_not_unique():
    notes = [("C", 0.0, 4), ("C", 0.0, 4), ("G", 0.0, 4)]
    card = vertical_cardinality_for_notes(notes, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 3
    assert card["vertical_unique_pitch_count"] == 2
    assert card["vertical_pitch_class_cardinality"] == 2


def test_vertical_cardinality_for_notes_chord_fields():
    card = vertical_cardinality_for_notes(MAJOR_TRIAD, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 3
    assert card["vertical_unique_pitch_count"] == 3
    assert card["vertical_pitch_class_cardinality"] == 3


def test_vertical_cardinality_for_notes_non_12tet_pc_cardinality_none():
    card = vertical_cardinality_for_notes(MAJOR_TRIAD, bin_cents=50, edo=24)
    assert card["vertical_note_count"] == 3
    assert card["vertical_unique_pitch_count"] == 3
    assert card["vertical_pitch_class_cardinality"] is None


def test_vertical_cardinality_for_notes_microtonal_pc_cardinality_none():
    card = vertical_cardinality_for_notes([("C", 0.5, 4)], bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 1
    assert card["vertical_unique_pitch_count"] == 1
    assert card["vertical_pitch_class_cardinality"] is None


def test_vertical_cardinality_from_summary_row_missing_and_invalid_fields():
    assert vertical_cardinality_from_summary_row({}, bin_cents=100, edo=12) == {
        "vertical_note_count": None,
        "vertical_unique_pitch_count": None,
        "vertical_pitch_class_cardinality": None,
    }
    row = {"Notes": "", "Unique pitches": "x", "PC cardinality": "bad"}
    card = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert card["vertical_note_count"] is None
    assert card["vertical_unique_pitch_count"] is None
    assert card["vertical_pitch_class_cardinality"] is None


def test_vertical_cardinality_from_summary_row_non_scalar_notes_typeerror():
    card = vertical_cardinality_from_summary_row(
        {"Notes": [2, 3]},
        bin_cents=100,
        edo=12,
    )
    assert card["vertical_note_count"] is None
    assert card["vertical_unique_pitch_count"] is None


def test_vertical_cardinality_from_summary_row_unique_falls_back_to_notes():
    row = {"Notes": 4}
    card = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 4
    assert card["vertical_unique_pitch_count"] == 4
    assert card["vertical_pitch_class_cardinality"] is None


def test_build_vertical_cardinality_series_preserves_order_and_fallback_time():
    rows = [
        {"Slice": 1, "Time (quarters)": 0.0, "Notes": 2, "Unique pitches": 2, "PC cardinality": 2},
        {"Slice": 2, "Time": "bad-time", "Notes": 3, "Unique pitches": 3, "PC cardinality": 3},
        {
            "Slice": 3,
            "Time": "2.0-4.0",
            "Time (quarters)": 3.0,
            "Notes": 4,
            "Unique pitches": 4,
            "PC cardinality": 4,
        },
    ]
    series = build_vertical_cardinality_series(rows, bin_cents=100, edo=12)
    assert len(series) == 3
    assert [s["slice_index"] for s in series] == [0, 1, 2]
    assert series[0]["time_quarters"] == pytest.approx(0.0)
    assert series[1]["time_quarters"] == pytest.approx(1.0)
    assert series[2]["time_quarters"] == pytest.approx(3.0)
    assert [s["vertical_note_count"] for s in series] == [2, 3, 4]


def test_build_vertical_cardinality_profile_empty_series():
    profile = build_vertical_cardinality_profile(
        deduplication_active=False,
        edo=12,
        bin_cents=100,
    )
    assert profile["series"] == []
    stats = profile["summary_statistics"]
    assert stats["n_slices"] == 0
    assert stats["min_vertical_note_count"] is None
    assert stats["mean_vertical_note_count"] is None


def test_build_vertical_cardinality_profile_summary_statistics_all_none_counts():
    rows = [{"Slice": 1, "Time (quarters)": 0.0, "Notes": ""}]
    profile = build_vertical_cardinality_profile(
        deduplication_active=False,
        edo=12,
        bin_cents=100,
        summary_rows=rows,
    )
    assert len(profile["series"]) == 1
    assert profile["series"][0]["vertical_note_count"] is None
    stats = profile["summary_statistics"]
    assert stats["n_slices"] == 1
    assert stats["min_vertical_note_count"] is None
    assert stats["std_vertical_note_count"] is None


@pytest.mark.parametrize(
    ("analysis_mode", "expected_label"),
    [
        (None, "unknown"),
        ("manual", "manual"),
        ("aggregate", "manual"),
        ("not-a-real-mode", "unknown"),
        (MusicXmlImportMode.ONSET_VERTICALITIES, "onset_verticalities"),
        (MusicXmlImportMode.SOUNDING_VERTICALITIES, "sounding_verticalities"),
        (MusicXmlImportMode.AGGREGATE, "manual"),
    ],
)
def test_build_vertical_cardinality_profile_analysis_mode_labels(
    analysis_mode, expected_label
):
    profile = build_vertical_cardinality_profile(
        analysis_mode=analysis_mode,
        deduplication_active=True,
        edo=12,
        bin_cents=100,
        aggregate_notes=MAJOR_TRIAD,
    )
    assert profile["source"]["analysis_mode"] == expected_label


def test_build_vertical_cardinality_profile_output_structure():
    rows = [
        enrich_slice_summary_row(
            {"Slice": 1, "Time (quarters)": 0.0},
            MAJOR_TRIAD,
            bin_cents=100,
            edo=12,
        ),
        enrich_slice_summary_row(
            {"Slice": 2, "Time (quarters)": 1.0},
            [("C", 0.0, 4), ("C", 0.0, 5)],
            bin_cents=100,
            edo=12,
        ),
    ]
    profile = build_vertical_cardinality_profile(
        input_file="test.xml",
        analysis_mode=MusicXmlImportMode.ONSET_VERTICALITIES,
        deduplication_active=False,
        edo=12,
        bin_cents=100,
        summary_rows=rows,
    )
    assert profile["schema_version"] == VERTICAL_CARDINALITY_SCHEMA_VERSION
    assert profile["metric_family"] == "vertical_cardinality"
    assert profile["time_unit"] == "quarters"
    assert set(profile["definitions"]) == set(DEFINITIONS)
    assert profile["source"]["input_file"] == "test.xml"
    assert profile["source"]["deduplication_active"] is False
    assert profile["source"]["edo"] == 12
    assert len(profile["series"]) == 2
    assert profile["summary_statistics"]["min_vertical_note_count"] == 2
    assert profile["summary_statistics"]["max_vertical_note_count"] == 3


def test_vertical_cardinality_profile_json_roundtrip():
    profile = build_vertical_cardinality_profile(
        analysis_mode="manual",
        deduplication_active=False,
        edo=12,
        bin_cents=100,
        aggregate_notes=MAJOR_TRIAD,
    )
    text = vertical_cardinality_profile_json(profile)
    payload = json.loads(text)
    assert payload["series"][0]["vertical_note_count"] == 3
    assert payload["source"]["analysis_mode"] == "manual"


def test_enrich_slice_summary_row_sets_expected_keys():
    row: dict = {"Slice": 1, "Time (quarters)": 0.0}
    out = enrich_slice_summary_row(row, MAJOR_TRIAD, bin_cents=100, edo=12)
    assert out is row
    assert out["Notes"] == 3
    assert out["Unique pitches"] == 3
    assert out["PC cardinality"] == 3
