"""MusicXML parser dispatch (written vs concert pitch)."""

from __future__ import annotations

from pathlib import Path

from iav.analysis_enums import MusicXmlImportMode
from iav.musicxml_io import parse_musicxml_upload

ROOT = Path(__file__).resolve().parent.parent
TRANSPOSE_FIXTURE = ROOT / "validation" / "fixtures" / "transpose.xml"


def test_aggregate_written_ignores_transpose():
    notes, skipped = parse_musicxml_upload(
        TRANSPOSE_FIXTURE.read_bytes(),
        MusicXmlImportMode.AGGREGATE,
        include_grace=False,
        include_cue=False,
        apply_sounding_transpose=False,
    )
    assert skipped == 0
    assert len(notes) == 1
    assert notes[0][0] == "C" and notes[0][1] == 0.0 and notes[0][2] == 4


def test_aggregate_sounding_applies_transpose():
    notes, skipped = parse_musicxml_upload(
        TRANSPOSE_FIXTURE.read_bytes(),
        MusicXmlImportMode.AGGREGATE,
        include_grace=False,
        include_cue=False,
        apply_sounding_transpose=True,
    )
    assert skipped == 0
    assert len(notes) == 1
    assert notes[0][0] == "D" and notes[0][1] == 0.0 and notes[0][2] == 4
