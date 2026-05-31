"""Headline H must match the selected intervallic concentration mode."""

from __future__ import annotations

import math

import pytest

from iav.analysis_enums import HomogeneityMethod, IntervallicHeadlineMode
from iav.interval_analysis_core import homogeneity_score, metrics_for_notes

_NOTES = [
    ("C", 0.0, 4),
    ("C", 1.0, 4),
    ("D", 0.0, 4),
    ("D", 1.0, 4),
    ("E", 0.0, 4),
    ("F", 0.0, 4),
]

_THRESH = (0.35, 0.8, 0.3, 0.6)


@pytest.mark.parametrize(
    "headline,expected_attr",
    [
        (IntervallicHeadlineMode.PAIRWISE, "pair_score"),
        (IntervallicHeadlineMode.ADJACENT, "chain_score"),
        (IntervallicHeadlineMode.WEIGHTED_LINEAR, "weighted_linear_score"),
        (IntervallicHeadlineMode.WEIGHTED_QUADRATIC, "weighted_quadratic_score"),
    ],
)
def test_headline_h_equals_component_score(headline, expected_attr):
    m = metrics_for_notes(
        _NOTES,
        *_THRESH,
        "entropy",
        bin_cents=100,
        intervallic_headline_mode=headline,
    )
    assert m["intervallic_headline_mode"] == headline.value
    assert m["H"] == pytest.approx(m[expected_attr])


def test_hybrid_headline_blend():
    alpha = 0.6
    m = metrics_for_notes(
        _NOTES,
        *_THRESH,
        "entropy",
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.HYBRID,
    )
    expected = alpha * m["chain_score"] + (1.0 - alpha) * m["pair_score"]
    assert m["H"] == pytest.approx(expected)
    assert m["hybrid_alpha_used"] == pytest.approx(alpha)


def test_combined_consensus_geometric_mean():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    m = metrics_for_notes(
        notes,
        *_THRESH,
        HomogeneityMethod.COMBINED.value,
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    assert m["H_dom"] is not None
    assert m["H_ent"] is not None
    assert m["H_consensus"] == pytest.approx(
        math.sqrt(max(0.0, m["H_dom"]) * max(0.0, m["H_ent"]))
    )
    assert m["H"] == pytest.approx(m["H_consensus"])


def test_homogeneity_score_headline_matches_metrics_for_notes():
    h, chain, pair, *_rest = homogeneity_score(
        _NOTES,
        alpha=0.6,
        method="entropy",
        bin_cents=100,
        headline_mode=IntervallicHeadlineMode.ADJACENT,
    )
    m = metrics_for_notes(
        _NOTES,
        *_THRESH,
        "entropy",
        bin_cents=100,
        intervallic_headline_mode=IntervallicHeadlineMode.ADJACENT,
    )
    assert h == pytest.approx(chain)
    assert m["H"] == pytest.approx(h)
    assert m["H"] == pytest.approx(m["chain_score"])
