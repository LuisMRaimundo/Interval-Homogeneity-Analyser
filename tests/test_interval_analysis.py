"""Tests for interval aggregates and 12-TET set-class helpers."""

import pitch_model
from interval_analysis import (
    chromatic_midi_float,
    format_note_display_label,
    format_note_spelling,
    interval_vector_12tet,
    metrics_for_notes,
    normal_order_12tet,
    prime_form_12tet,
    set_class_summary_12tet,
)


def test_chromatic_midi_matches_pitch_model():
    assert chromatic_midi_float is pitch_model.chromatic_midi_float
    assert chromatic_midi_float("A", 0.0, 4) == pitch_model.chromatic_midi_float("A", 0.0, 4)


def test_format_note_display_label_accidentals():
    assert format_note_display_label("C", 0.0, 4) == "C4"
    assert format_note_display_label("D", 1.0, 4) == "D#4"
    assert format_note_display_label("B", -1.0, 3) == "Bb3"
    assert format_note_display_label("C", 0.5, 5) == "C+5"
    assert format_note_display_label("F", 1.23, 2) == "F(+1.23st)2"


def test_format_note_spelling_matches_display_without_octave():
    assert format_note_spelling("C", 0.0) == "C"
    assert format_note_spelling("E", -1.0) == "Eb"
    assert format_note_display_label("G", 1.0, 5) == f"{format_note_spelling('G', 1.0)}5"


def test_major_triad_prime_and_iv():
    pcs = [0, 4, 7]
    # Forte prime form is the lexicographically smallest T/TnI form; major ≡ minor set-class → (0,3,7).
    assert prime_form_12tet(pcs) == (0, 3, 7)
    assert interval_vector_12tet(pcs) == [0, 0, 1, 1, 1, 0]


def test_minor_triad_prime():
    pcs = [0, 3, 7]
    assert prime_form_12tet(pcs) == (0, 3, 7)


def test_diminished_seventh_prime():
    pcs = [0, 3, 6, 9]
    assert prime_form_12tet(pcs) == (0, 3, 6, 9)


def test_normal_order_major():
    assert normal_order_12tet([0, 4, 7]) == (0, 4, 7)


def test_set_class_summary_from_notes():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    s = set_class_summary_12tet(notes)
    assert s is not None
    assert s["prime_form"] == (0, 3, 7)
    assert s["interval_vector"] == [0, 0, 1, 1, 1, 0]


def test_microtonal_returns_none_summary():
    notes = [("C", 0.5, 4), ("E", 0.0, 4)]
    assert set_class_summary_12tet(notes) is None


def test_metrics_bin_cents_non_default():
    notes = [("C", 0.0, 4), ("C", 0.0, 5)]
    m100 = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "dominance", bin_cents=100)
    m50 = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "dominance", bin_cents=50)
    assert m100["total_intervals"] == 1
    assert m50["total_intervals"] == 1
    assert m100["distance_counts"] != m50["distance_counts"]
