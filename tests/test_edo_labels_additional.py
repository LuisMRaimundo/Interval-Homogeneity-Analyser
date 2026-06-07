"""Focused tests for ``iav.interval_analysis_core._edo_labels``."""

from __future__ import annotations

import pytest

from iav.interval_analysis_core._edo_labels import (
    format_note_display_label,
    format_note_spelling,
    interval_name,
    intervals_for_notes,
    note_to_units,
    parse_manual_note_string,
    parse_note_name,
    quantize_units,
    semitone_to_label,
    units_to_label,
)


@pytest.mark.parametrize("note_name", ["", "   ", "\t"])
def test_parse_note_name_empty_or_whitespace_returns_none(note_name: str):
    assert parse_note_name(note_name) is None


def test_parse_note_name_rejects_octave_shorthand():
    assert parse_note_name("C4") is None
    assert parse_note_name("d4") is None


def test_parse_note_name_rejects_invalid_letter():
    assert parse_note_name("H4") is None


def test_parse_note_name_rejects_digit_accidental_suffix():
    assert parse_note_name("C2") is None
    assert parse_note_name("C 4") is None


@pytest.mark.parametrize(
    ("note_name", "expected"),
    [
        ("C", ("C", 0.0)),
        ("D#", ("D", 1.0)),
        ("Eb", ("E", -1.0)),
        ("Fbb", ("F", -2.0)),
        ("C+", ("C", 0.5)),
        ("C+0.5", ("C", 0.5)),
    ],
)
def test_parse_note_name_supported_accidentals(note_name, expected):
    assert parse_note_name(note_name) == expected


def test_parse_note_name_x_token_doubles_sharp():
    assert parse_note_name("Cx") == ("C", 2.0)


def test_parse_note_name_invalid_accidental_text_returns_none():
    assert parse_note_name("Cbogus") is None
    assert parse_note_name("C++") is None


def test_parse_note_name_numeric_accidental_without_token():
    assert parse_note_name("C0.25") == ("C", 0.25)


def test_parse_manual_note_string_empty_returns_none():
    assert parse_manual_note_string("") is None
    assert parse_manual_note_string("   ") is None


def test_parse_manual_note_string_invalid_letter_returns_none():
    assert parse_manual_note_string("H4") is None


def test_parse_manual_note_string_bad_default_octave_falls_back_to_four():
    assert parse_manual_note_string("C", default_octave="bad") == ("C", 0.0, 4)


def test_parse_manual_note_string_uses_default_octave_when_missing():
    assert parse_manual_note_string("Bb", default_octave=3) == ("B", -1.0, 3)


def test_parse_manual_note_string_explicit_octave_overrides_default():
    assert parse_manual_note_string("C#5", default_octave=2) == ("C", 1.0, 5)


def test_parse_manual_note_string_octave_only_tail():
    assert parse_manual_note_string("G5", default_octave=2) == ("G", 0.0, 5)


def test_parse_manual_note_string_unparseable_returns_none():
    assert parse_manual_note_string("H#4") is None
    assert parse_manual_note_string("Cbogus4") is None


def test_parse_manual_note_string_plus_accidental_with_octave():
    assert parse_manual_note_string("C+4") == ("C", 0.5, 4)


def test_parse_manual_note_string_flat_accidentals():
    assert parse_manual_note_string("Eb5") == ("E", -1.0, 5)
    assert parse_manual_note_string("Fbb3") == ("F", -2.0, 3)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.4, 0),
        (0.5, 1),
        (0.6, 1),
        (1.1, 1),
        (-0.4, 0),
        (-0.5, -1),
        (-0.6, -1),
        (-1.1, -1),
    ],
)
def test_quantize_units_rounding_rule(value, expected):
    assert quantize_units(value) == expected


def test_note_to_units_basic_and_accidentals():
    c4 = note_to_units("C", 0.0, 4, bin_cents=100)
    d4 = note_to_units("D", 0.0, 4, bin_cents=100)
    c_sharp4 = note_to_units("C", 1.0, 4, bin_cents=100)
    assert c4 == 60
    assert d4 == 62
    assert c_sharp4 == 61
    assert isinstance(note_to_units("E", -1.0, 4, bin_cents=100), int)
    assert c4 < c_sharp4 < d4


def test_note_to_units_respects_non_100_bin_cents():
    c4 = note_to_units("C", 0.0, 4, bin_cents=50)
    assert c4 == note_to_units("C", 0.0, 4, bin_cents=100) * 2


def test_semitone_to_label_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        semitone_to_label(-1)


@pytest.mark.parametrize(
    ("semitones", "expected"),
    [
        (0, "P1"),
        (4, "M3"),
        (6, "TT4"),
        (7, "P5"),
        (12, "P8"),
        (14, "M9"),
    ],
)
def test_semitone_to_label_mapping(semitones, expected):
    assert semitone_to_label(semitones) == expected


def test_units_to_label_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        units_to_label(-1)


def test_units_to_label_100_cent_delegates_to_semitone_labels():
    assert units_to_label(0, bin_cents=100) == "P1"
    assert units_to_label(7, bin_cents=100) == "P5"


def test_units_to_label_non_100_cent_returns_cents_string():
    assert units_to_label(2, bin_cents=50) == "100c"
    assert units_to_label(1, bin_cents=24) == "24c"
    assert units_to_label(0, bin_cents=50) == "0c"
    assert units_to_label(12, bin_cents=50) == "600c"


def test_format_note_spelling_known_accidental_token():
    assert format_note_spelling("C", 1.0) == "C#"
    assert format_note_spelling("B", -1.0) == "Bb"


def test_format_note_spelling_microtonal_fallback():
    assert format_note_spelling("C", 0.25) == "C(+0.25st)"


def test_format_note_spelling_fallback_when_symbol_not_in_preference(monkeypatch):
    monkeypatch.setattr(
        "iav.interval_analysis_core._edo_labels.ACC_TO_SEMITONES",
        {"": 0.0, "weird": 1.0},
    )
    assert format_note_spelling("C", 1.0) == "Cweird"


def test_format_note_display_label_includes_octave():
    assert format_note_display_label("C", 0.0, 4) == "C4"
    assert format_note_display_label("C", 1.0, 4) == "C#4"


def test_interval_name_orders_pitches_and_labels_distance():
    lower = ("C", 0.0, 4)
    upper = ("G", 0.0, 4)
    name, diff = interval_name(upper, lower, bin_cents=100)
    assert diff == 7
    assert name == "P5"


def test_intervals_for_notes_counts_pairwise_labels():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    interval_counts, distance_counts = intervals_for_notes(notes, bin_cents=100)
    assert sum(interval_counts.values()) == 3
    assert sum(distance_counts.values()) == 3
    assert "M3" in interval_counts
    assert "P5" in interval_counts
