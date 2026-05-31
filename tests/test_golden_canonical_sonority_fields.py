"""Canonical sonority bundle: extended field consistency (frozen JSON unchanged)."""

from __future__ import annotations

import pytest

from iav.analysis_enums import IntervallicHeadlineMode
from iav.canonical_corpus import analyze_sonority, load_canonical_corpus, verify_sonority_metrics
from iav.interval_analysis_core import metrics_for_notes


@pytest.fixture(scope="module")
def corpus_bundle():
    return load_canonical_corpus()


def _metrics_for_spec(notes, cfg):
    return metrics_for_notes(
        notes,
        0.35,
        0.8,
        0.3,
        cfg.hybrid_alpha,
        cfg.homogeneity_method,
        bin_cents=cfg.bin_cents,
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )


@pytest.mark.parametrize(
    "sonority_id",
    [
        "dyad_perfect_fifth",
        "chromatic_cluster_semitone",
        "major_triad_closed",
        "whole_tone_scale",
    ],
)
def test_canonical_metrics_bundle_aligns_with_frozen(corpus_bundle, sonority_id: str):
    cfg, specs = corpus_bundle
    spec = specs[sonority_id]
    computed = analyze_sonority(
        spec.notes,
        hybrid_alpha=cfg.hybrid_alpha,
        homogeneity_method=cfg.homogeneity_method,
        bin_cents=cfg.bin_cents,
    )
    verify_sonority_metrics(computed, spec.expected, sonority_id, tolerance=1e-3)
    m = _metrics_for_spec(spec.notes, cfg)
    assert m["H"] == pytest.approx(computed["H_headline_pairwise"], abs=1e-3)
    assert m["pair_score"] == pytest.approx(computed["pair_score"], abs=1e-3)
    assert m["chain_score"] == pytest.approx(computed["chain_score"], abs=1e-3)
    assert m["weighted_linear_score"] == pytest.approx(computed["weighted_linear_score"], abs=1e-3)
    assert m["weighted_quadratic_score"] == pytest.approx(computed["weighted_quadratic_score"], abs=1e-3)
    assert m["H_label"] == computed["H_label"]
    assert m["intervallic_headline_mode"] == cfg.headline_mode
    assert m["hybrid_alpha_used"] == pytest.approx(cfg.hybrid_alpha)
    assert sum(m["interval_counts"].values()) == m["total_intervals"]
    assert sum(m["distance_counts"].values()) == m["total_intervals"]
    assert sum(m["adj_counts"].values()) == max(0, len(spec.notes) - 1)
