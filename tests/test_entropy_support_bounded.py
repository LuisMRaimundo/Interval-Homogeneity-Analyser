"""Support-bounded entropy concentration invariants (TECHNICAL_MANUAL §4.4)."""

from __future__ import annotations

import pytest

from interval_analysis import (
    entropy_evenness,
    entropy_evenness_supportbounded,
    homogeneity_score,
    metrics_for_notes,
    pairwise_distance_support_bins,
)


def test_single_observed_category_concentration_one_entropy_mode():
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    h, _, pair, _, dc, _, *_ = homogeneity_score(notes, alpha=0.5, method="entropy", bin_cents=100)
    assert pair == pytest.approx(1.0)
    assert h == pytest.approx(1.0)
    assert dc == {4: 1}


def test_support_bounded_single_bin_evenness_zero():
    assert entropy_evenness_supportbounded({4: 3}, 10) == 0.0


def test_support_bounded_uniform_three_bins():
    counts = {0: 1, 1: 1, 2: 1}
    assert entropy_evenness_supportbounded(counts, 3) == pytest.approx(1.0)


def test_span_norm_stricter_than_category_count_norm():
    counts_int = {2: 2, 4: 1}
    counts_str = {"a": 2, "b": 1}
    span_even = entropy_evenness_supportbounded(counts_int, 5)
    obs_even = entropy_evenness(counts_str)
    assert span_even < obs_even


def test_pairwise_support_bins_span_plus_one():
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    assert pairwise_distance_support_bins(notes, 100) == 4 + 1


def test_evenness_score_uses_support_bins_in_metrics():
    notes = [("C", 0.0, 4), ("C", 1.0, 4), ("D", 0.0, 4), ("E", 0.0, 4)]
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "entropy", bin_cents=100)
    support = m["pairwise_entropy_support_bins"]
    assert support == pairwise_distance_support_bins(notes, 100)
    recomputed = entropy_evenness_supportbounded(m["distance_counts"], support)
    assert m["evenness_score"] == pytest.approx(recomputed)


def test_empty_counts_intervallic_concentration_zero():
    from iav.interval_analysis_core import intervallic_concentration

    assert intervallic_concentration({}, "entropy", 5) == 0.0
    assert intervallic_concentration({}, "dominance", 5) == 0.0


def test_dyad_entropy_concentration_equals_one_minus_evenness():
    notes = [("C", 0.0, 4), ("G", 0.0, 4)]
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "entropy", bin_cents=100)
    assert m["evenness_score"] == pytest.approx(0.0)
    assert m["pair_score"] == pytest.approx(1.0)
