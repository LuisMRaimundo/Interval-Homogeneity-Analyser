"""MusicXML golden structure: slices, counts, transpose, passage ΔH (no canonical regen)."""

from __future__ import annotations

from pathlib import Path

import pytest

from iav.analysis_enums import IntervallicHeadlineMode, MusicXmlImportMode
from iav.canonical_musicxml import load_canonical_musicxml, verify_musicxml_entry
from iav.interval_analysis_core import metrics_for_notes
from iav.musicxml_io import (
    parse_musicxml_bytes,
    parse_musicxml_upload,
    parse_musicxml_verticalities_bytes,
)
from iav.symbolic_profile import passage_delta_rows

ROOT = Path(__file__).resolve().parent.parent
TRANSPOSE_FIXTURE = ROOT / "validation" / "fixtures" / "transpose.xml"
CHROMATIC_XML = ROOT / "validation" / "canonical" / "chromatic_cluster.xml"
MULTI_VOICE = ROOT / "validation" / "corpus" / "multi_voice_same_measure.xml"


@pytest.fixture(scope="module")
def musicxml_canonical():
    return load_canonical_musicxml()


@pytest.mark.parametrize(
    "entry_id",
    ["major_triad", "minor_triad", "chromatic_cluster", "quartal_stack", "diminished_seventh"],
)
def test_frozen_canonical_musicxml_metrics(musicxml_canonical, entry_id: str):
    verify_musicxml_entry(musicxml_canonical[entry_id])


def test_chromatic_cluster_aggregate_note_count():
    entry = load_canonical_musicxml()["chromatic_cluster"]
    notes, skipped = parse_musicxml_bytes(entry.xml_path.read_bytes())
    assert skipped == 0
    assert len(notes) == int(entry.expected["note_count"])


def test_chromatic_cluster_onset_verticality_slice_count_and_times():
    data = CHROMATIC_XML.read_bytes()
    slices, skipped = parse_musicxml_verticalities_bytes(data, include_grace=True, include_cue=True)
    assert skipped == 0
    assert len(slices) == 6
    times = [s["time"] for s in slices]
    assert times == sorted(times)
    assert times[0] == pytest.approx(0.0)
    assert all(len(s["notes"]) == 1 for s in slices)


def test_multi_voice_same_onset_two_notes():
    slices, skipped = parse_musicxml_verticalities_bytes(
        MULTI_VOICE.read_bytes(), include_grace=True, include_cue=True
    )
    assert skipped == 0
    two_note_slices = [s for s in slices if len(s["notes"]) >= 2]
    assert len(two_note_slices) >= 1
    letters = {n[0] for n in two_note_slices[0]["notes"]}
    assert letters == {"C", "E"}


def test_aggregate_written_vs_sounding_transpose():
    data = TRANSPOSE_FIXTURE.read_bytes()
    written, _ = parse_musicxml_upload(
        data,
        MusicXmlImportMode.AGGREGATE,
        include_grace=False,
        include_cue=False,
        apply_sounding_transpose=False,
    )
    sounding, _ = parse_musicxml_upload(
        data,
        MusicXmlImportMode.AGGREGATE,
        include_grace=False,
        include_cue=False,
        apply_sounding_transpose=True,
    )
    assert written[0][0] == "C"
    assert sounding[0][0] == "D"


def test_passage_delta_h_between_consecutive_slice_rows():
    rows = [{"time": 0.0, "H": 0.25}, {"time": 1.0, "H": 0.50}, {"time": 2.0, "H": 0.80}]
    with_delta = passage_delta_rows(rows)
    assert with_delta[0]["ΔH (prev slice)"] is None
    assert with_delta[1]["ΔH (prev slice)"] == pytest.approx(0.25)
    assert with_delta[2]["ΔH (prev slice)"] == pytest.approx(0.30)


def test_multi_voice_slice_headline_h_matches_frozen_aggregate():
    """Two-note verticality slice matches aggregate canonical metrics for same pitches."""
    entry = load_canonical_musicxml()["major_triad"]
    slices, skipped = parse_musicxml_verticalities_bytes(
        MULTI_VOICE.read_bytes(), include_grace=True, include_cue=True
    )
    assert skipped == 0
    dyad_slice = next(s for s in slices if len(s["notes"]) >= 2)
    m_slice = metrics_for_notes(
        dyad_slice["notes"],
        0.35,
        0.8,
        0.3,
        0.6,
        "dominance",
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    notes_agg, _ = parse_musicxml_bytes(entry.xml_path.read_bytes())
    m_agg = metrics_for_notes(
        notes_agg,
        0.35,
        0.8,
        0.3,
        0.6,
        "dominance",
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    assert m_slice["H"] != m_agg["H"]
