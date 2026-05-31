"""Pairwise-only H, span-based entropy normalization, and optional chain blend."""

import math

from interval_analysis import (
    IntervallicHeadlineMode,
    entropy_evenness,
    entropy_evenness_supportbounded,
    homogeneity_score,
    metrics_for_notes,
    pairwise_distance_support_bins,
)


def test_pairwise_distance_support_bins_dyad():
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    assert pairwise_distance_support_bins(notes, 100) == 4 + 1


def test_entropy_supportbounded_uniform_matches_one():
    counts = {0: 1, 1: 1, 2: 1}
    e = entropy_evenness_supportbounded(counts, 3)
    assert abs(e - 1.0) < 1e-9


def test_entropy_supportbounded_singleton_zero_evenness():
    assert entropy_evenness_supportbounded({4: 3}, 10) == 0.0


def test_span_norm_stricter_than_observed_category_count():
    """Same histogram: normalizing by ln(5) yields lower evenness than normalizing by ln(2)."""
    counts_int = {2: 2, 4: 1}
    counts_str = {"a": 2, "b": 1}  # two observed labels for entropy_evenness
    span_even = entropy_evenness_supportbounded(counts_int, 5)
    obs_even = entropy_evenness(counts_str)
    assert span_even < obs_even


def test_headline_h_is_pairwise_when_blend_off():
    notes = [
        ("C", 0.0, 4),
        ("C", 1.0, 4),
        ("D", 0.0, 4),
        ("D", 1.0, 4),
        ("E", 0.0, 4),
    ]
    m = metrics_for_notes(
        notes,
        0.35,
        0.8,
        0.3,
        0.7,
        "entropy",
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    assert m["H"] == m["pair_score"]
    assert m["chain_score"] == 1.0
    assert m["pair_score"] < 1.0


def test_hybrid_headline_changes_h_when_chain_differs_from_pair():
    notes = [
        ("C", 0.0, 4),
        ("C", 1.0, 4),
        ("D", 0.0, 4),
        ("D", 1.0, 4),
        ("E", 0.0, 4),
    ]
    h_hybrid, c_on, p_on, *_ = homogeneity_score(
        notes,
        alpha=0.5,
        method="entropy",
        bin_cents=100,
        headline_mode=IntervallicHeadlineMode.HYBRID,
    )
    h_pair, c_off, p_off, *_ = homogeneity_score(
        notes,
        alpha=0.5,
        method="entropy",
        bin_cents=100,
        headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    assert h_pair == p_off
    assert abs(h_hybrid - (0.5 * c_on + 0.5 * p_on)) < 1e-9
    assert h_hybrid > h_pair


def test_evenness_score_uses_distance_histogram_not_labels():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "dominance", bin_cents=100)
    assert m["pairwise_entropy_support_bins"] == pairwise_distance_support_bins(notes, 100)
    label_even = entropy_evenness(m["interval_counts"])
    assert not math.isclose(
        float(m["evenness_score"]), float(label_even), rel_tol=1e-6, abs_tol=1e-6
    )
