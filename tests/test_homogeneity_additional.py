"""Focused tests for ``iav.interval_analysis_core._homogeneity``."""

from __future__ import annotations

import math

import pytest

from iav.analysis_enums import IntervallicHeadlineMode
from iav.interval_analysis_core._homogeneity import (
    cluster_compactness,
    dominance,
    dominance_weighted,
    entropy_evenness,
    entropy_evenness_supportbounded,
    entropy_evenness_supportbounded_weighted,
    homogeneity_score,
    intervallic_concentration,
    proximity_weighted_distance_counts,
    type_concentration,
)


def test_cluster_compactness_single_note_fallback():
    notes = [("C", 0.0, 4)]
    compactness, span_cents, avg_distance = cluster_compactness(notes, bin_cents=100)
    assert compactness == 1.0
    assert span_cents == 0
    assert avg_distance == 0.0


def test_cluster_compactness_identical_pitches_zero_span():
    notes = [("C", 0.0, 4), ("C", 0.0, 4)]
    compactness, span_cents, avg_distance = cluster_compactness(notes, bin_cents=100)
    assert compactness == 1.0
    assert span_cents == 0
    assert avg_distance == 0.0


def test_cluster_compactness_nonzero_span():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    compactness, span_cents, avg_distance = cluster_compactness(notes, bin_cents=100)
    assert compactness == pytest.approx(1.0 / 3.0)
    assert span_cents == 700
    assert avg_distance == pytest.approx(1400.0 / 3.0)


def test_type_concentration_empty_returns_zero():
    assert type_concentration({}) == 0.0


def test_type_concentration_total_at_most_one_returns_one():
    assert type_concentration({"M3": 1}) == 1.0


def test_type_concentration_single_type_multiple_counts_is_maximal():
    assert type_concentration({"P5": 5}) == 1.0


def test_type_concentration_multiple_types_lower_than_maximal():
    assert type_concentration({"M3": 2, "P5": 2}) == pytest.approx(2.0 / 3.0)


def test_entropy_evenness_empty_returns_zero():
    assert entropy_evenness({}) == 0.0


def test_entropy_evenness_single_category_returns_zero():
    assert entropy_evenness({"M3": 4}) == 0.0


def test_entropy_evenness_balanced_higher_than_concentrated():
    balanced = entropy_evenness({"M3": 2, "P5": 2})
    concentrated = entropy_evenness({"M3": 10, "P5": 1})
    assert balanced == pytest.approx(1.0)
    assert concentrated < balanced


def test_dominance_empty_returns_zero():
    assert dominance({}) == 0.0


def test_dominance_non_empty_share_of_largest_count():
    assert dominance({7: 3, 4: 1}) == pytest.approx(0.75)


def test_dominance_zero_total_returns_zero():
    assert dominance({7: 0, 4: 0}) == 0.0


def test_dominance_weighted_empty_returns_zero():
    assert dominance_weighted({}) == 0.0


def test_dominance_weighted_non_empty_share_of_largest_weight():
    assert dominance_weighted({7: 3.0, 4: 1.0}) == pytest.approx(0.75)


def test_dominance_weighted_zero_total_returns_zero():
    assert dominance_weighted({7: 0.0, 4: 0.0}) == 0.0


def test_entropy_evenness_supportbounded_empty_returns_zero():
    assert entropy_evenness_supportbounded({}, support_bins=5) == 0.0


def test_entropy_evenness_supportbounded_non_positive_total_returns_zero():
    assert entropy_evenness_supportbounded({1: 0, 2: 0}, support_bins=5) == 0.0


def test_entropy_evenness_supportbounded_support_bins_at_most_one_returns_zero():
    assert entropy_evenness_supportbounded({1: 2, 2: 1}, support_bins=1) == 0.0
    assert entropy_evenness_supportbounded({1: 2, 2: 1}, support_bins=0) == 0.0


def test_entropy_evenness_supportbounded_balanced_higher_than_concentrated():
    balanced = entropy_evenness_supportbounded({1: 1, 2: 1, 3: 1}, support_bins=3)
    concentrated = entropy_evenness_supportbounded({1: 9, 2: 1}, support_bins=3)
    assert balanced == pytest.approx(1.0)
    assert concentrated < balanced


def test_entropy_evenness_supportbounded_weighted_empty_returns_zero():
    assert entropy_evenness_supportbounded_weighted({}, support_bins=5) == 0.0


def test_entropy_evenness_supportbounded_weighted_non_positive_total_returns_zero():
    assert entropy_evenness_supportbounded_weighted({1: 0.0}, support_bins=5) == 0.0


def test_entropy_evenness_supportbounded_weighted_support_bins_at_most_one_returns_zero():
    assert entropy_evenness_supportbounded_weighted({1: 1.0, 2: 1.0}, support_bins=1) == 0.0


def test_entropy_evenness_supportbounded_weighted_balanced_higher_than_concentrated():
    balanced = entropy_evenness_supportbounded_weighted(
        {1: 1.0, 2: 1.0, 3: 1.0}, support_bins=3
    )
    concentrated = entropy_evenness_supportbounded_weighted(
        {1: 100.0, 2: 1.0}, support_bins=3
    )
    assert balanced == pytest.approx(math.log(3) / math.log(3))
    assert concentrated < balanced


def test_intervallic_concentration_weighted_dominance_path():
    counts = proximity_weighted_distance_counts(
        [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)],
        bin_cents=100,
        inverse_power=1,
    )
    assert intervallic_concentration(counts, "dominance", support_bins=5) == pytest.approx(
        dominance_weighted(counts)
    )


def test_intervallic_concentration_weighted_entropy_path():
    counts = proximity_weighted_distance_counts(
        [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)],
        bin_cents=100,
        inverse_power=2,
    )
    expected = 1.0 - entropy_evenness_supportbounded_weighted(counts, 5)
    assert intervallic_concentration(counts, "entropy", support_bins=5) == pytest.approx(
        expected
    )


@pytest.mark.parametrize("alpha", [-0.01, 1.01])
def test_homogeneity_score_rejects_alpha_out_of_range(alpha: float):
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    with pytest.raises(ValueError, match="alpha must be between 0 and 1"):
        homogeneity_score(notes, alpha=alpha)


def test_homogeneity_score_rejects_invalid_method():
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    with pytest.raises(ValueError, match="method must be 'dominance' or 'entropy'"):
        homogeneity_score(notes, alpha=0.5, method="variance")


def test_homogeneity_score_dominance_method_dyad():
    notes = [("C", 0.0, 4), ("G", 0.0, 4)]
    h, chain, pair, *_ = homogeneity_score(notes, alpha=0.5, method="dominance")
    assert pair == 1.0
    assert chain == 1.0
    assert h == 1.0


def test_homogeneity_score_entropy_method_dyad():
    notes = [("C", 0.0, 4), ("G", 0.0, 4)]
    h, chain, pair, *_ = homogeneity_score(notes, alpha=0.5, method="entropy")
    assert pair == 1.0
    assert chain == 1.0
    assert h == 1.0


def test_homogeneity_score_adjacent_headline_mode():
    notes = [("C", 0.0, 4), ("C", 1.0, 4), ("D", 0.0, 4)]
    h, chain, pair, *_ = homogeneity_score(
        notes,
        alpha=0.5,
        method="entropy",
        headline_mode=IntervallicHeadlineMode.ADJACENT,
    )
    assert h == chain
