"""Canonical MIDI spelling and respelling (shared with MusicXML transpose)."""

import pytest

from pitch_model import (
    AnalyzedPitch,
    chromatic_midi_float,
    midis_from_spellings,
    spelled_note_from_chromatic_midi,
)


def test_chromatic_midi_middle_c():
    assert chromatic_midi_float("C", 0.0, 4) == 60.0


def test_spelled_note_roundtrip():
    t = spelled_note_from_chromatic_midi(60.0)
    assert t == ("C", 0.0, 4)
    assert chromatic_midi_float(*t) == 60.0


def test_transpose_plus_two_respells_to_d():
    assert spelled_note_from_chromatic_midi(60.0 + 2.0) == ("D", 0.0, 4)


def test_analyzed_pitch_from_spelling():
    p = AnalyzedPitch.from_spelling("E", -1.0, 4)
    assert abs(p.midi_semitones - 63.0) < 1e-9
    assert p.spelling == ("E", -1.0, 4)


def test_midis_from_spellings():
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    assert midis_from_spellings(notes) == [60.0, 64.0]


@pytest.mark.parametrize(
    "midi,expected",
    [
        (71.0, ("B", 0.0, 4)),
        (71.0 + 12.0, ("B", 0.0, 5)),
    ],
)
def test_octave_change_style_total(midi, expected):
    assert spelled_note_from_chromatic_midi(midi) == expected
