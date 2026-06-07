"""Focused tests for ``iav.musicxml_io._xml_primitives``."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from iav.musicxml_io._xml_primitives import (
    extract_pitch_from_note,
    tie_types_from_note,
    transpose_from_attributes,
)
from iav.pitch_model import ACCIDENTAL_TOKENS, MICROTONAL_ACCIDENTALS

# Public helper is ``extract_pitch_from_note`` (no separate ``parse_pitch``).


def _sub(tag: str, text: str | None = None) -> ET.Element:
    elem = ET.Element(tag)
    if text is not None:
        elem.text = text
    return elem


def _note(*children: ET.Element) -> ET.Element:
    note = ET.Element("note")
    for child in children:
        note.append(child)
    return note


def _pitch(step: str | None = None, octave: str | None = None, alter: str | None = None) -> ET.Element:
    pitch = ET.Element("pitch")
    if step is not None:
        pitch.append(_sub("step", step))
    if alter is not None:
        pitch.append(_sub("alter", alter))
    if octave is not None:
        pitch.append(_sub("octave", octave))
    return pitch


def test_extract_pitch_from_note_missing_pitch_returns_none():
    assert extract_pitch_from_note(_note(_sub("duration", "1"))) == (None, 0)


@pytest.mark.parametrize(
    "pitch",
    [
        _pitch(octave="4"),
        _pitch(step="C"),
        _pitch(step="C", octave=None),
    ],
)
def test_extract_pitch_from_note_missing_step_or_octave_returns_none(pitch: ET.Element):
    assert extract_pitch_from_note(_note(pitch)) == (None, 0)


def test_extract_pitch_from_note_invalid_step_returns_none():
    note = _note(_pitch(step="H", octave="4"))
    assert extract_pitch_from_note(note) == (None, 0)


def test_extract_pitch_from_note_invalid_octave_returns_none():
    note = _note(_pitch(step="C", octave="bad"))
    assert extract_pitch_from_note(note) == (None, 0)


def test_extract_pitch_from_note_invalid_alter_increments_skipped():
    note = _note(_pitch(step="C", octave="4", alter="bad"))
    assert extract_pitch_from_note(note) == (None, 1)


@pytest.mark.parametrize(
    ("accidental", "expected_alter"),
    [
        ("sharp", 1.0),
        ("flat", -1.0),
        ("natural", 0.0),
    ],
)
def test_extract_pitch_from_note_accidental_tokens_set_alter(accidental, expected_alter):
    note = _note(_pitch(step="F", octave="4"), _sub("accidental", accidental))
    parsed, skipped = extract_pitch_from_note(note)
    assert skipped == 0
    assert parsed is not None
    assert parsed[0] == "F"
    assert parsed[1] == pytest.approx(expected_alter)
    assert parsed[2] == 4


def test_extract_pitch_from_note_invalid_accidental_increments_skipped():
    note = _note(_pitch(step="C", octave="4"), _sub("accidental", "not-a-token"))
    assert extract_pitch_from_note(note) == (None, 1)


def test_extract_pitch_from_note_microtonal_accidental_with_zero_alter():
    note = _note(
        _pitch(step="C", octave="5", alter="0"),
        _sub("accidental", "quarter-sharp"),
    )
    parsed, skipped = extract_pitch_from_note(note)
    assert skipped == 0
    assert parsed == ("C", 0.5, 5)


def test_extract_pitch_from_note_microtonal_accidental_keeps_explicit_nonzero_alter():
    note = _note(
        _pitch(step="D", octave="7", alter="1"),
        _sub("accidental", "quarter-flat"),
    )
    parsed, skipped = extract_pitch_from_note(note)
    assert skipped == 0
    assert parsed == ("D", 1.0, 7)


def test_extract_pitch_from_note_microtonal_token_membership():
    assert "quarter-sharp" in MICROTONAL_ACCIDENTALS
    assert ACCIDENTAL_TOKENS["quarter-sharp"] == pytest.approx(0.5)


def test_extract_pitch_from_note_applies_transpose_semitones():
    note = _note(_pitch(step="D", octave="4"))
    parsed, skipped = extract_pitch_from_note(note, transpose_semitones=-2.0)
    assert skipped == 0
    assert parsed == ("C", 0.0, 4)


def test_extract_pitch_from_note_zero_transpose_is_noop():
    note = _note(_pitch(step="E", octave="3"))
    assert extract_pitch_from_note(note, transpose_semitones=0.0) == (("E", 0.0, 3), 0)


def test_tie_types_from_note_empty_when_no_tie_markup():
    assert tie_types_from_note(_note(_pitch(step="C", octave="4"))) == set()


def test_tie_types_from_note_direct_tie_elements():
    note = ET.Element("note")
    note.append(_sub("tie"))
    note[0].set("type", "start")
    note.append(_sub("tie"))
    note[1].set("type", "stop")
    assert tie_types_from_note(note) == {"start", "stop"}


def test_tie_types_from_note_notations_tied_elements():
    note = ET.Element("note")
    notations = ET.Element("notations")
    tied = ET.Element("tied")
    tied.set("type", "continue")
    notations.append(tied)
    note.append(notations)
    assert tie_types_from_note(note) == {"continue"}


def test_tie_types_from_note_combines_direct_and_notations():
    note = ET.Element("note")
    tie = _sub("tie")
    tie.set("type", "start")
    note.append(tie)
    notations = ET.Element("notations")
    tied = ET.Element("tied")
    tied.set("type", "stop")
    notations.append(tied)
    note.append(notations)
    assert tie_types_from_note(note) == {"start", "stop"}


def test_transpose_from_attributes_none_returns_zero():
    assert transpose_from_attributes(None) == 0.0


def test_transpose_from_attributes_without_transpose_returns_zero():
    attrs = ET.Element("attributes")
    attrs.append(_sub("divisions", "1"))
    assert transpose_from_attributes(attrs) == 0.0


def test_transpose_from_attributes_chromatic_only():
    attrs = ET.Element("attributes")
    transpose = ET.Element("transpose")
    transpose.append(_sub("chromatic", "-2"))
    attrs.append(transpose)
    assert transpose_from_attributes(attrs) == pytest.approx(-2.0)


def test_transpose_from_attributes_octave_change_only():
    attrs = ET.Element("attributes")
    transpose = ET.Element("transpose")
    transpose.append(_sub("octave-change", "1"))
    attrs.append(transpose)
    assert transpose_from_attributes(attrs) == pytest.approx(12.0)


def test_transpose_from_attributes_chromatic_and_octave_change_combined():
    attrs = ET.Element("attributes")
    transpose = ET.Element("transpose")
    transpose.append(_sub("chromatic", "2"))
    transpose.append(_sub("octave-change", "-1"))
    attrs.append(transpose)
    assert transpose_from_attributes(attrs) == pytest.approx(-10.0)


def test_transpose_from_attributes_invalid_chromatic_is_ignored():
    attrs = ET.Element("attributes")
    transpose = ET.Element("transpose")
    transpose.append(_sub("chromatic", "bad"))
    transpose.append(_sub("octave-change", "1"))
    attrs.append(transpose)
    assert transpose_from_attributes(attrs) == pytest.approx(12.0)


def test_transpose_from_attributes_invalid_octave_change_is_ignored():
    attrs = ET.Element("attributes")
    transpose = ET.Element("transpose")
    transpose.append(_sub("chromatic", "3"))
    transpose.append(_sub("octave-change", "n/a"))
    attrs.append(transpose)
    assert transpose_from_attributes(attrs) == pytest.approx(3.0)
