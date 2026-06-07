"""Focused tests for ``iav.symbolic_profile``."""

from __future__ import annotations

import pytest

from iav.symbolic_profile import (
    _catalog_note_tuple,
    _headline_h_column,
    _load_reference_catalog,
    compare_to_references,
    entropy_evenness_counts,
    histogram_l1_distance,
    ic_evenness_from_notes,
    normalized_distance_histogram,
    passage_delta_rows,
    reference_catalog,
)


def test_entropy_evenness_counts_empty_returns_zero():
    assert entropy_evenness_counts({}) == 0.0


def test_entropy_evenness_counts_single_category_returns_zero():
    assert entropy_evenness_counts({3: 4}) == 0.0


def test_entropy_evenness_counts_balanced_interval_vector_finite():
    counts = {1: 1, 2: 1, 3: 1}
    evenness = entropy_evenness_counts(counts)
    assert 0.0 < evenness <= 1.0


def test_ic_evenness_from_notes_microtonal_returns_none():
    evenness, cardinality = ic_evenness_from_notes([("C", 0.5, 4), ("E", 0.0, 4)])
    assert evenness is None
    assert cardinality is None


def test_ic_evenness_from_notes_single_pitch_class_returns_none_evenness():
    evenness, cardinality = ic_evenness_from_notes([("C", 0.0, 4)])
    assert evenness is None
    assert cardinality == 1


def test_ic_evenness_from_notes_empty_notes_returns_none_cardinality():
    evenness, cardinality = ic_evenness_from_notes([])
    assert evenness is None
    assert cardinality is None


def test_ic_evenness_from_notes_major_triad_finite_evenness():
    evenness, cardinality = ic_evenness_from_notes(
        [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    )
    assert cardinality == 3
    assert evenness is not None
    assert 0.0 <= evenness <= 1.0


def test_ic_evenness_from_notes_repeated_pitch_classes_deduplicated():
    with_repeat = ic_evenness_from_notes(
        [("C", 0.0, 4), ("C", 0.0, 5), ("E", 0.0, 4), ("G", 0.0, 4)]
    )
    without_repeat = ic_evenness_from_notes(
        [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    )
    assert with_repeat == without_repeat


def test_normalized_distance_histogram_empty_returns_empty_dict():
    assert normalized_distance_histogram({}) == {}


def test_normalized_distance_histogram_non_positive_total_returns_empty_dict():
    assert normalized_distance_histogram({2: 0, 4: 0}) == {}


def test_normalized_distance_histogram_valid_counts_sum_to_one():
    hist = normalized_distance_histogram({2: 2, 4: 2})
    assert hist == {2: 0.5, 4: 0.5}
    assert sum(hist.values()) == pytest.approx(1.0)


def test_normalized_distance_histogram_preserves_zero_count_entries():
    hist = normalized_distance_histogram({2: 2, 4: 0})
    assert hist == {2: 1.0, 4: 0.0}


def test_histogram_l1_distance_identical_histograms_zero():
    hist = {1: 0.5, 2: 0.5}
    assert histogram_l1_distance(hist, hist) == 0.0


def test_histogram_l1_distance_disjoint_histograms():
    assert histogram_l1_distance({1: 1.0}, {2: 1.0}) == pytest.approx(2.0)


def test_histogram_l1_distance_partial_overlap():
    a = {1: 0.5, 2: 0.5}
    b = {1: 1.0}
    assert histogram_l1_distance(a, b) == pytest.approx(1.0)


_FAKE_REFERENCE_CATALOG = {
    "perfect_fifth": {
        "label": "Perfect fifth",
        "notes": [["C", 0.0, 4], ["G", 0.0, 4]],
        "edo": 12,
    },
    "major_third": {
        "label": "Major third",
        "notes": [["C", 0.0, 4], ["E", 0.0, 4]],
        "edo": 12,
    },
    "single_letter_names": {
        "label": "Single-letter catalog spelling",
        "notes": [["C", 0.0, 4], ["G", 0.0, 4]],
        "edo": 12,
    },
    "wrong_edo": {
        "label": "24-EDO reference",
        "notes": [["C", 0.0, 4], ["G", 0.0, 4]],
        "edo": 24,
    },
    "too_few_notes": {
        "label": "Singleton",
        "notes": [["C", 0.0, 4]],
        "edo": 12,
    },
}


def test_catalog_note_tuple_single_letter_name_uses_alter_field():
    assert _catalog_note_tuple(["C", 0.0, 4]) == ("C", 0.0, 4)


def test_load_reference_catalog_missing_file_returns_empty(monkeypatch):
    class _MissingPath:
        def is_file(self):
            return False

    monkeypatch.setattr("iav.symbolic_profile._REFERENCE_PATH", _MissingPath())
    assert _load_reference_catalog() == {}
    assert reference_catalog() == {}


def test_compare_to_references_empty_catalog_returns_empty_tuple(monkeypatch):
    monkeypatch.setattr(
        "iav.symbolic_profile._load_reference_catalog",
        lambda: {},
    )
    assert compare_to_references({7: 1}, edo=12) == ()


def test_compare_to_references_empty_distance_counts_returns_empty_tuple(monkeypatch):
    monkeypatch.setattr(
        "iav.symbolic_profile._load_reference_catalog",
        lambda: _FAKE_REFERENCE_CATALOG,
    )
    assert compare_to_references({}, edo=12) == ()


def test_compare_to_references_skips_mismatched_edo_and_invalid_entries(monkeypatch):
    monkeypatch.setattr(
        "iav.symbolic_profile._load_reference_catalog",
        lambda: _FAKE_REFERENCE_CATALOG,
    )
    results = compare_to_references({7: 1}, edo=12, top_n=10)
    ids = {item[0] for item in results}
    assert "wrong_edo" not in ids
    assert "too_few_notes" not in ids
    assert ids <= {"perfect_fifth", "major_third", "single_letter_names"}


def test_compare_to_references_scores_valid_references_sorted_ascending(monkeypatch):
    monkeypatch.setattr(
        "iav.symbolic_profile._load_reference_catalog",
        lambda: _FAKE_REFERENCE_CATALOG,
    )
    results = compare_to_references({7: 1}, edo=12, top_n=10)
    assert results
    assert results[0][0] == "perfect_fifth"
    assert results[0][2] == pytest.approx(0.0)
    distances = [item[2] for item in results]
    assert distances == sorted(distances)


def test_compare_to_references_top_n_limits_result_count(monkeypatch):
    monkeypatch.setattr(
        "iav.symbolic_profile._load_reference_catalog",
        lambda: _FAKE_REFERENCE_CATALOG,
    )
    results = compare_to_references({7: 1}, edo=12, top_n=1)
    assert len(results) == 1


def test_headline_h_column_prefers_consensus_key():
    row = {"H (interval dominance)": 0.5, "H (consensus)": 0.6}
    assert _headline_h_column(row) == "H (consensus)"


def test_headline_h_column_first_h_paren_key():
    row = {"Slice": 1, "H (interval dominance)": 0.5}
    assert _headline_h_column(row) == "H (interval dominance)"


def test_headline_h_column_plain_h_key():
    row = {"Slice": 1, "H": 0.5}
    assert _headline_h_column(row) == "H"


def test_headline_h_column_missing_returns_none():
    assert _headline_h_column({"Slice": 1, "pair_score": 0.5}) is None


def test_passage_delta_rows_empty_returns_empty_list():
    assert passage_delta_rows([]) == []


def test_passage_delta_rows_single_row_adds_none_delta():
    row = {"Slice": 1, "H": 0.5}
    out = passage_delta_rows([row])
    assert len(out) == 1
    assert out[0]["ΔH (prev slice)"] is None
    assert out[0]["Slice"] == 1
    assert out[0]["H"] == 0.5


def test_passage_delta_rows_two_rows_rounded_delta():
    rows = [{"Slice": 1, "H": 0.5}, {"Slice": 2, "H": 0.7123}]
    out = passage_delta_rows(rows)
    assert out[1]["ΔH (prev slice)"] == pytest.approx(0.212, abs=0.001)


def test_passage_delta_rows_invalid_h_values_yield_none_delta():
    rows = [{"Slice": 1, "H": "bad"}, {"Slice": 2, "H": 0.7}]
    out = passage_delta_rows(rows)
    assert out[1]["ΔH (prev slice)"] is None


def test_passage_delta_rows_uses_consensus_headline_column():
    rows = [
        {"Slice": 1, "H (consensus)": 0.4},
        {"Slice": 2, "H (consensus)": 0.9, "H": 0.1},
    ]
    out = passage_delta_rows(rows)
    assert out[1]["ΔH (prev slice)"] == pytest.approx(0.5)


def test_passage_delta_rows_preserves_original_row_fields():
    rows = [{"Slice": 1, "H": 0.5, "extra": "keep"}, {"Slice": 2, "H": 0.8, "extra": "stay"}]
    out = passage_delta_rows(rows)
    assert out[0]["extra"] == "keep"
    assert out[1]["extra"] == "stay"
    assert rows[0]["extra"] == "keep"
