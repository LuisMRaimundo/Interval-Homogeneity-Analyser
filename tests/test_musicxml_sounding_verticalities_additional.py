"""Focused tests for ``iav.musicxml_io._sounding_verticalities``."""

from __future__ import annotations

import inspect
import io
import zipfile
from pathlib import Path

import pytest

from iav.musicxml_io._sounding_verticalities import (
    parse_musicxml_sounding_verticalities_bytes,
    parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose,
)

ROOT = Path(__file__).resolve().parent.parent
TIE_DIRECT = ROOT / "validation" / "fixtures" / "tie_direct.xml"
TIE_NOTATIONS = ROOT / "validation" / "fixtures" / "tie_notations.xml"


def _score(body: str, *, part_id: str = "P1") -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<score-partwise version="3.1"><part id="{part_id}">{body}</part></score-partwise>'
    ).encode("utf-8")


def _measure(inner: str, *, number: str = "1", attributes: str = "<divisions>1</divisions>") -> str:
    return f'<measure number="{number}"><attributes>{attributes}</attributes>{inner}</measure>'


def _note(
    step: str,
    octave: int,
    *,
    duration: int = 1,
    chord: bool = False,
    tie: str | None = None,
    alter: str | None = None,
) -> str:
    chord_xml = "<chord/>" if chord else ""
    alter_xml = f"<alter>{alter}</alter>" if alter is not None else ""
    tie_xml = f'<tie type="{tie}"/>' if tie else ""
    return (
        f"<note>{chord_xml}<pitch><step>{step}</step>{alter_xml}<octave>{octave}</octave></pitch>"
        f"<duration>{duration}</duration>{tie_xml}</note>"
    )


def test_sustained_single_note_active_span():
    xml = _score(_measure(_note("C", 4, duration=2)))
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(xml)
    assert skipped == 0
    assert len(slices) == 1
    assert slices[0]["start"] == pytest.approx(0.0)
    assert slices[0]["end"] == pytest.approx(2.0)
    assert slices[0]["notes"] == [("C", 0.0, 4)]


def test_chord_simultaneous_notes_share_sounding_slice():
    inner = _note("C", 4) + _note("E", 4, chord=True) + _note("G", 4, chord=True)
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(_score(_measure(inner)))
    assert skipped == 0
    assert len(slices) == 1
    assert {n[0] for n in slices[0]["notes"]} == {"C", "E", "G"}
    assert slices[0]["start"] == pytest.approx(0.0)
    assert slices[0]["end"] == pytest.approx(1.0)


@pytest.mark.parametrize("fixture_path", [TIE_DIRECT, TIE_NOTATIONS])
def test_tied_notes_form_one_sustained_slice(fixture_path: Path):
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(fixture_path.read_bytes())
    assert skipped == 0
    assert len(slices) == 1
    assert slices[0] == {"start": 0.0, "end": 2.0, "notes": [("C", 0.0, 4)]}


def test_tie_across_measures_extends_single_active_span():
    body = (
        _measure(_note("C", 4, tie="start"))
        + _measure(_note("C", 4, tie="stop"), number="2", attributes="")
    )
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(_score(body))
    assert skipped == 0
    assert slices == [{"start": 0.0, "end": 2.0, "notes": [("C", 0.0, 4)]}]


def test_open_tie_start_without_stop_closes_at_recorded_end():
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(
        _score(_measure(_note("G", 3, duration=2, tie="start")))
    )
    assert skipped == 0
    assert slices == [{"start": 0.0, "end": 2.0, "notes": [("G", 0.0, 3)]}]


def test_tie_stop_without_open_tie_still_yields_local_slice():
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(
        _score(_measure(_note("D", 4, tie="stop")))
    )
    assert skipped == 0
    assert slices == [{"start": 0.0, "end": 1.0, "notes": [("D", 0.0, 4)]}]


def test_rest_only_score_returns_empty_slices():
    xml = _score(_measure("<note><rest/><duration>1</duration></note>"))
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(xml)
    assert slices == []
    assert skipped == 0


def test_invalid_alter_increments_skipped_microtonal():
    xml = _score(_measure(_note("C", 4, alter="bad")))
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(xml)
    assert slices == []
    assert skipped == 1


def test_no_xml_in_zip_returns_empty_slices():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", b"no score")
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(buf.getvalue())
    assert slices == []
    assert skipped == 0


def test_written_pitch_ignores_transpose():
    body = _measure(
        _note("D", 4),
        attributes="<divisions>1</divisions><transpose><chromatic>-2</chromatic></transpose>",
    )
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(_score(body))
    assert skipped == 0
    assert slices[0]["notes"] == [("D", 0.0, 4)]


def test_sounding_transpose_wrapper_applies_concert_pitch():
    body = _measure(
        _note("D", 4),
        attributes="<divisions>1</divisions><transpose><chromatic>-2</chromatic></transpose>",
    )
    xml = _score(body)
    written, _ = parse_musicxml_sounding_verticalities_bytes(xml)
    sounding, skipped = parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose(xml)
    assert skipped == 0
    assert written[0]["notes"] == [("D", 0.0, 4)]
    assert sounding[0]["notes"] == [("C", 0.0, 4)]


def test_sounding_verticalities_parser_has_no_grace_or_cue_flags():
    """Characterization: unlike onset verticalities, sounding API has no include_grace/include_cue."""
    sig_plain = inspect.signature(parse_musicxml_sounding_verticalities_bytes)
    sig_transpose = inspect.signature(
        parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose
    )
    assert list(sig_plain.parameters) == ["file_bytes"]
    assert list(sig_transpose.parameters) == ["file_bytes"]
