"""Vertical symbolic cardinality profile and timeline (not intervallic H)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("altair")

from iav.analysis_enums import MusicXmlImportMode
from iav.charts import (
    chart_homogeneity_over_time,
    chart_vertical_cardinality_over_time,
    vertical_cardinality_timeline_dataframe,
)
from iav.interval_analysis_core import dedupe_notes_by_midi, metrics_for_notes
from iav.musicxml_io import parse_musicxml_verticalities_bytes
from iav.vertical_cardinality import (
    VERTICAL_CARDINALITY_SCHEMA_VERSION,
    build_vertical_cardinality_profile,
    build_vertical_cardinality_series,
    enrich_slice_summary_row,
    vertical_cardinality_for_notes,
    vertical_cardinality_from_summary_row,
)

ROOT = Path(__file__).resolve().parent.parent
MAJOR_TRIAD = ROOT / "validation" / "canonical" / "major_triad.xml"
QUARTAL = ROOT / "validation" / "canonical" / "quartal_stack.xml"
PASSAGE_VARYING_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Test</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration></note>
      <note><chord/><pitch><step>E</step><octave>4</octave></pitch><duration>2</duration></note>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration></note>
      <note><chord/><pitch><step>E</step><octave>4</octave></pitch><duration>2</duration></note>
      <note><chord/><pitch><step>G</step><octave>4</octave></pitch><duration>2</duration></note>
      <note><pitch><step>C</step><octave>5</octave></pitch><duration>2</duration></note>
      <note><chord/><pitch><step>E</step><octave>5</octave></pitch><duration>2</duration></note>
      <note><chord/><pitch><step>G</step><octave>5</octave></pitch><duration>2</duration></note>
      <note><chord/><pitch><step>B</step><octave>5</octave></pitch><duration>2</duration></note>
    </measure>
  </part>
</score-partwise>
"""


def test_triad_vertical_note_count_three():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    card = vertical_cardinality_for_notes(notes, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 3
    assert card["vertical_unique_pitch_count"] == 3
    assert card["vertical_pitch_class_cardinality"] == 3


def test_four_note_aggregate_vertical_note_count_four():
    notes = [("C", 0.0, 4), ("F", 0.0, 4), ("B", -1.0, 4), ("E", -1.0, 5)]
    card = vertical_cardinality_for_notes(notes, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 4
    assert card["vertical_unique_pitch_count"] == 4


def test_deduplication_collapses_duplicate_pitches():
    notes = [("C", 0.0, 4), ("C", 0.0, 4), ("G", 0.0, 4)]
    deduped = dedupe_notes_by_midi(notes, bin_cents=100)
    card = vertical_cardinality_for_notes(deduped, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 2
    assert card["vertical_unique_pitch_count"] == 2
    assert len(notes) == 3
    row: dict = {"Slice": 1, "Time (quarters)": 0.0}
    enrich_slice_summary_row(row, deduped, bin_cents=100, edo=12)
    assert row["Notes"] == 2


def _build_slice_summary_rows(xml_path: Path) -> list[dict]:
    slices, _ = parse_musicxml_verticalities_bytes(
        xml_path.read_bytes(), include_grace=True, include_cue=True
    )
    rows: list[dict] = []
    for idx, s in enumerate(slices, start=1):
        notes = s["notes"]
        if len(notes) < 2:
            continue
        m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.6, "dominance", bin_cents=100)
        row = {
            "Slice": idx,
            "Time": f"{s['time']:.3f}",
            "Time (quarters)": float(s["time"]),
            "H (interval dominance)": round(m["H"], 3),
        }
        enrich_slice_summary_row(row, notes, bin_cents=100, edo=12)
        rows.append(row)
    return rows


def test_passage_timeline_note_counts_increase():
    slices, _ = parse_musicxml_verticalities_bytes(
        PASSAGE_VARYING_XML, include_grace=True, include_cue=True
    )
    rows: list[dict] = []
    for idx, s in enumerate(slices, start=1):
        notes = s["notes"]
        if len(notes) < 2:
            continue
        m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.6, "dominance", bin_cents=100)
        row = {
            "Slice": idx,
            "Time (quarters)": float(s["time"]),
            "H (interval dominance)": round(m["H"], 3),
        }
        enrich_slice_summary_row(row, notes, bin_cents=100, edo=12)
        rows.append(row)
    assert [r["Notes"] for r in rows] == [2, 3, 4]
    df = vertical_cardinality_timeline_dataframe(rows)
    assert list(df["vertical_note_count"]) == [2, 3, 4]


def test_json_export_schema_and_summary_statistics():
    rows = _build_slice_summary_rows(QUARTAL)
    if not rows:
        notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
        rows = [
            enrich_slice_summary_row(
                {"Slice": 1, "Time (quarters)": 0.0, "H (interval dominance)": 0.3},
                notes,
                bin_cents=100,
                edo=12,
            )
        ]
    profile = build_vertical_cardinality_profile(
        input_file="major_triad.xml",
        analysis_mode=MusicXmlImportMode.ONSET_VERTICALITIES,
        deduplication_active=False,
        edo=12,
        bin_cents=100,
        summary_rows=rows,
    )
    assert profile["schema_version"] == VERTICAL_CARDINALITY_SCHEMA_VERSION
    assert profile["metric_family"] == "vertical_cardinality"
    assert "definitions" in profile
    assert profile["definitions"]["vertical_note_count"]
    assert len(profile["series"]) == len(rows)
    stats = profile["summary_statistics"]
    assert stats["n_slices"] == len(rows)
    assert stats["min_vertical_note_count"] == 3
    assert stats["max_vertical_note_count"] == 3
    assert stats["mean_vertical_note_count"] == pytest.approx(3.0)
    assert stats["median_vertical_note_count"] == pytest.approx(3.0)
    payload = json.loads(json.dumps(profile))
    assert payload["series"][0]["vertical_note_count"] == rows[0]["Notes"]


def test_aggregate_manual_mode_single_slice_json():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    profile = build_vertical_cardinality_profile(
        analysis_mode="manual",
        deduplication_active=True,
        edo=12,
        bin_cents=100,
        aggregate_notes=notes,
    )
    assert len(profile["series"]) == 1
    assert profile["series"][0]["time_quarters"] == 0.0
    assert profile["series"][0]["vertical_note_count"] == 3
    assert profile["source"]["analysis_mode"] == "manual"


def test_vertical_chart_does_not_break_homogeneity_chart():
    rows = [
        {
            "Slice": 1,
            "Time": "0.000",
            "Time (quarters)": 0.0,
            "H (interval dominance)": 0.4,
            "Notes": 4,
        },
        {
            "Slice": 2,
            "Time": "1.000",
            "Time (quarters)": 1.0,
            "H (interval dominance)": 0.7,
            "Notes": 5,
        },
        {
            "Slice": 3,
            "Time": "2.000",
            "Time (quarters)": 2.0,
            "H (interval dominance)": 0.5,
            "Notes": 6,
        },
    ]
    assert chart_homogeneity_over_time(rows) is not None
    assert chart_vertical_cardinality_over_time(rows) is not None


def test_summary_row_notes_matches_json_series():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    row: dict = {"Slice": 1, "Time (quarters)": 0.0, "Time": "0.000"}
    enrich_slice_summary_row(row, notes, bin_cents=100, edo=12)
    series = build_vertical_cardinality_series([row], bin_cents=100, edo=12)
    assert series[0]["vertical_note_count"] == row["Notes"] == 3
    recovered = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert recovered["vertical_note_count"] == 3


def test_summary_row_missing_pc_cardinality_is_not_inferred() -> None:
    row = {"Notes": 2, "Unique pitches": 2}
    card = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 2
    assert card["vertical_unique_pitch_count"] == 2
    assert card["vertical_pitch_class_cardinality"] is None


def test_summary_row_without_pc_cardinality_returns_none() -> None:
    """Regression: no PC column → vertical_pitch_class_cardinality must be None."""
    row = {"Notes": 2, "Unique pitches": 2}
    recovered = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert recovered["vertical_pitch_class_cardinality"] is None


def test_summary_row_with_pc_cardinality_one_returns_one() -> None:
    row = {"Notes": 2, "Unique pitches": 2, "PC cardinality": 1}
    recovered = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert recovered["vertical_pitch_class_cardinality"] == 1


def test_pc_cardinality_not_inferred_when_column_missing():
    """C4+C5: unique pitch count can equal note count without implying one pitch class."""
    row = {
        "Slice": 1,
        "Time (quarters)": 0.0,
        "Notes": 2,
        "Unique pitches": 2,
    }
    recovered = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert recovered["vertical_note_count"] == 2
    assert recovered["vertical_unique_pitch_count"] == 2
    assert recovered["vertical_pitch_class_cardinality"] is None


def test_c4_c5_octave_duplicate_pitch_class_from_notes_not_inferred_in_json_row():
    notes = [("C", 0.0, 4), ("C", 0.0, 5)]
    card = vertical_cardinality_for_notes(notes, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 2
    assert card["vertical_unique_pitch_count"] == 2
    assert card["vertical_pitch_class_cardinality"] == 1

    row = {"Notes": 2, "Unique pitches": 2}
    from_row = vertical_cardinality_from_summary_row(row, bin_cents=100, edo=12)
    assert from_row["vertical_pitch_class_cardinality"] is None

    enriched = enrich_slice_summary_row(
        {"Slice": 1, "Time (quarters)": 0.0}, notes, bin_cents=100, edo=12
    )
    assert enriched["PC cardinality"] == 1
    assert (
        vertical_cardinality_from_summary_row(enriched, bin_cents=100, edo=12)[
            "vertical_pitch_class_cardinality"
        ]
        == 1
    )
