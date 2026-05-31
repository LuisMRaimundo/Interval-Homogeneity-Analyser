"""Regression against frozen canonical sonority expectations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from iav.canonical_corpus import (
    analyze_sonority,
    load_canonical_corpus,
    verify_sonority_metrics,
)

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def corpus_bundle():
    return load_canonical_corpus()


def test_corpus_has_minimum_cardinality(corpus_bundle):
    _cfg, specs = corpus_bundle
    assert len(specs) >= 10


@pytest.mark.parametrize(
    "sonority_id",
    [
        "dyad_perfect_fifth",
        "unison_duplicates",
        "chromatic_cluster_semitone",
        "whole_tone_scale",
        "quartal_stack",
        "major_triad_closed",
        "minor_triad_closed",
        "diminished_seventh",
        "augmented_triad",
        "octatonic_half_whole",
        "sparse_random_like",
        "wide_span_register",
        "dense_narrow_chromatic",
    ],
)
def test_canonical_sonority_matches_frozen_expectations(corpus_bundle, sonority_id: str):
    cfg, specs = corpus_bundle
    spec = specs[sonority_id]
    computed = analyze_sonority(
        spec.notes,
        hybrid_alpha=cfg.hybrid_alpha,
        homogeneity_method=cfg.homogeneity_method,
        bin_cents=cfg.bin_cents,
    )
    verify_sonority_metrics(computed, spec.expected, sonority_id, tolerance=1e-3)


def test_chromatic_cluster_adjacent_dominates_pairwise(corpus_bundle):
    _, specs = corpus_bundle
    spec = specs["chromatic_cluster_semitone"]
    c = analyze_sonority(spec.notes, bin_cents=100)
    assert c["chain_score"] >= 0.95
    assert c["pair_score"] < c["chain_score"]


def test_examples_corpus_json_files_match_bundle():
    """Each examples/corpus/*.json should match bundled analysis."""
    cfg, specs = load_canonical_corpus()
    examples_dir = ROOT / "examples" / "corpus"
    if not examples_dir.is_dir():
        pytest.skip("examples/corpus not present")
    for path in sorted(examples_dir.glob("*.json")):
        sid = path.stem
        if sid not in specs:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        notes = [tuple(n) for n in payload["notes"]]
        computed = analyze_sonority(
            notes,
            hybrid_alpha=cfg.hybrid_alpha,
            homogeneity_method=cfg.homogeneity_method,
            bin_cents=cfg.bin_cents,
        )
        verify_sonority_metrics(computed, specs[sid].expected, sid, tolerance=1e-3)
