"""Manual input parsing and hints."""

from interval_analysis import (
    looks_like_octave_shorthand_in_note_field,
    manual_input_hints,
    normalize_manual_notes,
    parse_manual_note_string,
    parse_note_name,
)


def test_shorthand_detected():
    assert looks_like_octave_shorthand_in_note_field("C4") is True
    assert looks_like_octave_shorthand_in_note_field("d4") is True
    assert looks_like_octave_shorthand_in_note_field("B9") is True
    assert looks_like_octave_shorthand_in_note_field("C 4") is True
    assert looks_like_octave_shorthand_in_note_field("g\t5") is True


def test_not_shorthand():
    assert looks_like_octave_shorthand_in_note_field("C") is False
    assert looks_like_octave_shorthand_in_note_field("C#") is False
    assert looks_like_octave_shorthand_in_note_field("Eb") is False
    assert looks_like_octave_shorthand_in_note_field("C+0.5") is False
    assert looks_like_octave_shorthand_in_note_field("") is False


def test_parse_note_name_still_rejects_octave_in_pitch_class_parser():
    assert parse_note_name("C4") is None
    assert parse_note_name("d4") is None


def test_parse_manual_note_string_combined():
    assert parse_manual_note_string("C4") == ("C", 0.0, 4)
    assert parse_manual_note_string("Eb5") == ("E", -1.0, 5)
    assert parse_manual_note_string("C#4") == ("C", 1.0, 4)
    assert parse_manual_note_string("C", default_octave=3) == ("C", 0.0, 3)
    assert parse_manual_note_string("C+4") == ("C", 0.5, 4)


def test_normalize_manual_notes_accepts_c4():
    rows = [{"Note": "C4"}, {"Note": "C#4"}]
    notes, errors = normalize_manual_notes(rows)
    assert notes == [("C", 0.0, 4), ("C", 1.0, 4)]
    assert errors == []


def test_normalize_legacy_octave_column():
    rows = [{"Note": "C", "Octave": 5}]
    notes, errors = normalize_manual_notes(rows)
    assert notes == [("C", 0.0, 5)]
    assert errors == []


def test_hints_duplicate_pitch_rows():
    rows = [{"Note": "C4"}, {"Note": "C4"}]
    h = manual_input_hints(rows)
    assert any("duplicate" in x.lower() for x in h)


def test_hints_unusual_octave():
    rows = [{"Note": "C0"}]
    h = manual_input_hints(rows)
    assert any("octave" in x.lower() and "0" in x for x in h)
