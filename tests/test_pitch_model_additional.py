"""Focused tests for ``iav.pitch_model`` octave normalisation in spelling."""

from __future__ import annotations

import pytest

from iav.pitch_model import chromatic_midi_float, spelled_note_from_chromatic_midi


def _assert_roundtrip(midi: float) -> None:
    spelling = spelled_note_from_chromatic_midi(midi)
    assert chromatic_midi_float(*spelling) == pytest.approx(midi)


def test_spelled_note_in_octave_middle_c_unchanged():
    assert spelled_note_from_chromatic_midi(60.0) == ("C", 0.0, 4)
    _assert_roundtrip(60.0)


def test_downward_octave_wrap_c4_minus_one_semitone():
    midi = chromatic_midi_float("C", 0.0, 4) - 1.0
    assert spelled_note_from_chromatic_midi(midi) == ("B", 0.0, 3)
    _assert_roundtrip(midi)


def test_upward_octave_wrap_b4_plus_one_semitone():
    midi = chromatic_midi_float("B", 0.0, 4) + 1.0
    assert spelled_note_from_chromatic_midi(midi) == ("C", 0.0, 5)
    _assert_roundtrip(midi)


def test_multiple_octave_downward_wrap():
    midi = chromatic_midi_float("C", 0.0, 4) - 13.0
    assert spelled_note_from_chromatic_midi(midi) == ("B", 0.0, 2)
    _assert_roundtrip(midi)

    midi_two_octaves = chromatic_midi_float("C", 0.0, 4) - 24.0
    assert spelled_note_from_chromatic_midi(midi_two_octaves) == ("C", 0.0, 2)
    _assert_roundtrip(midi_two_octaves)


def test_multiple_octave_upward_wrap():
    midi = chromatic_midi_float("B", 0.0, 4) + 13.0
    assert spelled_note_from_chromatic_midi(midi) == ("C", 0.0, 6)
    _assert_roundtrip(midi)

    midi_two_octaves = chromatic_midi_float("C", 0.0, 4) + 24.0
    assert spelled_note_from_chromatic_midi(midi_two_octaves) == ("C", 0.0, 6)
    _assert_roundtrip(midi_two_octaves)


def test_boundary_rem_zero_does_not_change_octave():
    assert spelled_note_from_chromatic_midi(60.0) == ("C", 0.0, 4)
    assert spelled_note_from_chromatic_midi(72.0) == ("C", 0.0, 5)


def test_boundary_rem_just_below_twelve_stays_in_octave():
    midi = chromatic_midi_float("B", 0.0, 4) + 0.999999999
    spelling = spelled_note_from_chromatic_midi(midi)
    assert spelling[0] == "B"
    assert spelling[2] == 4
    _assert_roundtrip(midi)


def test_boundary_twelfth_semitone_crosses_to_next_octave():
    midi = chromatic_midi_float("B", 0.0, 4) + 1.0
    assert spelled_note_from_chromatic_midi(midi) == ("C", 0.0, 5)


def test_defensive_downward_rem_loop_on_large_midi_float():
    """Floating-point residue can fall below zero at extreme magnitudes."""
    midi = float(2**56 - 5)
    spelling = spelled_note_from_chromatic_midi(midi)
    assert spelling == ("E", 0.0, 6004799503160659)


def test_defensive_upward_rem_loop_on_large_midi_float():
    """Floating-point residue can reach twelve or more at extreme magnitudes."""
    midi = float(2**57 - 41)
    spelling = spelled_note_from_chromatic_midi(midi)
    assert spelling == ("E", 0.0, 12009599006321318)
