"""Intervallic profile: reference fingerprints and passage ΔH (not registral metrics)."""

from interval_analysis import metrics_for_notes
from iav.symbolic_profile import (
    intervallic_profile_for_notes,
    passage_delta_rows,
    reference_catalog,
)


def test_reference_catalog_loads():
    cat = reference_catalog()
    assert "major_triad_closed" in cat
    assert "label" in cat["major_triad_closed"]


def test_chromatic_cluster_matches_reference_best():
    notes = [
        ("C", 0.0, 4),
        ("C", 1.0, 4),
        ("D", 0.0, 4),
        ("D", 1.0, 4),
        ("E", 0.0, 4),
    ]
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "dominance", bin_cents=100)
    profile = intervallic_profile_for_notes(
        notes, edo=12, distance_counts=m["distance_counts"]
    )
    assert profile.reference_comparisons
    assert profile.reference_comparisons[0][0] == "chromatic_cluster_5"


def test_passage_delta_appends_dh_only():
    rows = [
        {"Slice": 1, "H": 0.5},
        {"Slice": 2, "H": 0.7},
    ]
    out = passage_delta_rows(rows)
    assert out[0]["ΔH (prev slice)"] is None
    assert out[1]["ΔH (prev slice)"] == 0.2
    assert "Δ span" not in out[1]


def test_passage_delta_single_row_gets_column():
    rows = [{"Slice": 1, "H (interval dominance)": 0.5}]
    out = passage_delta_rows(rows)
    assert len(out) == 1
    assert out[0]["ΔH (prev slice)"] is None
