"""Sensitivity of hybrid H and classifications to α (documented heuristics)."""

from __future__ import annotations

import pytest

from iav.analysis_enums import IntervallicHeadlineMode
from iav.canonical_corpus import load_canonical_corpus
from iav.interval_analysis_core import homogeneity_score, metrics_for_notes


@pytest.mark.parametrize("alpha", [0.3, 0.4, 0.5, 0.6, 0.7])
def test_chromatic_cluster_chain_score_invariant_in_alpha(alpha: float):
    _, specs = load_canonical_corpus()
    notes = specs["chromatic_cluster_semitone"].notes
    _h, chain, pair, *_ = homogeneity_score(
        notes,
        alpha=alpha,
        method="dominance",
        bin_cents=100,
        headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    assert chain == 1.0
    assert pair < 0.5


@pytest.mark.parametrize("alpha", [0.3, 0.4, 0.5, 0.6, 0.7])
def test_hybrid_monotone_in_alpha_for_chromatic_cluster(alpha: float):
    _, specs = load_canonical_corpus()
    notes = specs["chromatic_cluster_semitone"].notes
    h, chain, pair, *_ = homogeneity_score(
        notes,
        alpha=alpha,
        method="dominance",
        bin_cents=100,
        headline_mode=IntervallicHeadlineMode.HYBRID,
    )
    expected = alpha * chain + (1.0 - alpha) * pair
    assert abs(h - expected) < 1e-9


def test_hybrid_ordering_across_alpha_major_triad_stable_headline_band():
    _, specs = load_canonical_corpus()
    notes = specs["major_triad_closed"].notes
    labels = []
    for alpha in (0.3, 0.5, 0.7):
        m = metrics_for_notes(
            notes,
            0.35,
            0.8,
            0.3,
            alpha,
            "dominance",
            bin_cents=100,
            intervallic_headline_mode=IntervallicHeadlineMode.HYBRID,
        )
        labels.append(m["H_label"])
    assert len(set(labels)) == 1, f"H_label varied: {labels}"
