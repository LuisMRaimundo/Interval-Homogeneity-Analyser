"""Adjacent, weighted, and hybrid intervallic headline modes."""

from interval_analysis import (
    IntervallicHeadlineMode,
    homogeneity_score,
    metrics_for_notes,
)


def _chromatic_stack_notes():
    return [
        ("C", 0.0, 4),
        ("C", 1.0, 4),
        ("D", 0.0, 4),
        ("D", 1.0, 4),
        ("E", 0.0, 4),
        ("F", 0.0, 4),
    ]


def test_chromatic_cluster_adjacent_headline_max_pairwise_lower():
    notes = _chromatic_stack_notes()
    m_adj = metrics_for_notes(
        notes,
        0.35,
        0.8,
        0.3,
        0.6,
        "entropy",
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.ADJACENT,
    )
    m_pair = metrics_for_notes(
        notes,
        0.35,
        0.8,
        0.3,
        0.6,
        "entropy",
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    assert m_adj["chain_score"] == 1.0
    assert m_adj["H"] == 1.0
    assert m_pair["pair_score"] < 1.0
    assert m_pair["H"] == m_pair["pair_score"]
    assert m_adj["weighted_linear_score"] > m_pair["pair_score"]


def test_hybrid_alpha_blend():
    notes = _chromatic_stack_notes()
    h, chain, pair, *_ = homogeneity_score(
        notes,
        alpha=0.6,
        method="entropy",
        bin_cents=100,
        headline_mode=IntervallicHeadlineMode.HYBRID,
    )
    assert abs(h - (0.6 * chain + 0.4 * pair)) < 1e-9
    assert h > pair


def test_proximity_weighted_between_adjacent_and_pairwise():
    notes = _chromatic_stack_notes()
    m = metrics_for_notes(
        notes,
        0.35,
        0.8,
        0.3,
        0.5,
        "dominance",
        bin_cents=100,
    )
    assert m["chain_score"] >= m["weighted_quadratic_score"] >= m["pair_score"]
