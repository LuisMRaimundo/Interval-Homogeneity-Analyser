"""Empty / None / DataFrame manual table inputs must not raise."""

import pytest

from interval_analysis import manual_input_hints, normalize_manual_notes


def test_normalize_manual_notes_empty_inputs():
    assert normalize_manual_notes(None) == ([], [])
    assert normalize_manual_notes([]) == ([], [])


def test_manual_input_hints_empty_inputs():
    assert manual_input_hints(None) == []
    assert manual_input_hints([]) == []


def test_normalize_and_hints_empty_dataframe():
    pd = pytest.importorskip("pandas")
    empty = pd.DataFrame()
    assert normalize_manual_notes(empty) == ([], [])
    assert manual_input_hints(empty) == []


def test_normalize_skips_blank_note_rows():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame([{"Note": ""}, {"Note": "C4"}, {"Note": "E4"}])
    notes, errors = normalize_manual_notes(df)
    assert notes == [("C", 0.0, 4), ("E", 0.0, 4)]
    assert errors == []
