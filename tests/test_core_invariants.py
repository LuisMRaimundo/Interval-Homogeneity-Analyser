"""Mathematical and structural invariants (no golden value changes)."""

from __future__ import annotations

import itertools
import random

import pytest

from iav.analysis_enums import IntervallicHeadlineMode
from iav.interval_analysis_core import (
    dedupe_notes_by_midi,
    metrics_for_notes,
    note_to_units,
)
from iav.pitch_model import chromatic_midi_float

_CHROMATIC_STACK = [
    ("C", 0.0, 4),
    ("C", 1.0, 4),
    ("D", 0.0, 4),
    ("D", 1.0, 4),
    ("E", 0.0, 4),
]


def _metrics(notes, *, method: str = "entropy", headline=IntervallicHeadlineMode.PAIRWISE):
    return metrics_for_notes(
        notes,
        0.35,
        0.8,
        0.3,
        0.6,
        method,
        bin_cents=100,
        intervallic_headline_mode=headline,
    )


def test_permutation_invariance_pairwise_scores():
    notes = _CHROMATIC_STACK + [("F", 0.0, 4)]
    base = _metrics(notes)
    for perm in itertools.islice(itertools.permutations(notes), 12):
        m = _metrics(list(perm))
        assert m["pair_score"] == pytest.approx(base["pair_score"])
        assert m["chain_score"] == pytest.approx(base["chain_score"])
        assert m["weighted_linear_score"] == pytest.approx(base["weighted_linear_score"])
        assert m["weighted_quadratic_score"] == pytest.approx(base["weighted_quadratic_score"])
        assert m["evenness_score"] == pytest.approx(base["evenness_score"])
        assert m["distance_counts"] == base["distance_counts"]
        assert m["adj_counts"] == base["adj_counts"]


def test_transposition_invariance_whole_semitones():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    shifted = [("D", 0.0, 4), ("F", 1.0, 4), ("A", 0.0, 4)]
    m0 = _metrics(notes)
    m1 = _metrics(shifted)
    assert m0["H"] == pytest.approx(m1["H"])
    assert m0["pair_score"] == pytest.approx(m1["pair_score"])
    assert m0["chain_score"] == pytest.approx(m1["chain_score"])


def test_enharmonic_grid_distance_equivalence_12tet():
    notes_a = [("C", 1.0, 4), ("E", 0.0, 4)]
    notes_b = [("D", -1.0, 4), ("E", 0.0, 4)]
    assert note_to_units(*notes_a[0], 100) == note_to_units(*notes_b[0], 100)
    m_a = _metrics(notes_a)
    m_b = _metrics(notes_b)
    assert m_a["pair_score"] == pytest.approx(m_b["pair_score"])
    assert m_a["distance_counts"] == m_b["distance_counts"]


def test_duplicate_collapse_reduces_note_count_and_matches_deduped_aggregate():
    notes = [("C", 0.0, 4), ("C", 0.0, 4), ("G", 0.0, 4)]
    deduped = dedupe_notes_by_midi(notes, bin_cents=100)
    assert len(deduped) == 2
    m_dedup = _metrics(deduped)
    m_from_dedupe_path = _metrics(dedupe_notes_by_midi(notes, bin_cents=100))
    assert m_dedup["pair_score"] == pytest.approx(m_from_dedupe_path["pair_score"])
    assert len(notes) > len(deduped)


@pytest.mark.parametrize("edo", [12, 24, 48])
def test_edo_bin_cents_consistency_dyad(edo: int):
    bin_cents = int(round(1200 / edo))
    notes = [("C", 0.0, 4), ("G", 0.0, 4)]
    m = metrics_for_notes(
        notes,
        0.35,
        0.8,
        0.3,
        0.6,
        "dominance",
        bin_cents=bin_cents,
    )
    assert m["pair_score"] == pytest.approx(1.0)
    assert m["chain_score"] == pytest.approx(1.0)
    assert m["H"] == pytest.approx(1.0)


def test_single_note_pairless_metrics_zero_intervals():
    notes = [("C", 0.0, 4)]
    m = _metrics(notes)
    assert m["total_intervals"] == 0
    assert m["distance_counts"] == {}
    assert m["adj_counts"] == {}


def test_chromatic_midi_float_matches_note_to_units_12tet():
    for letter, alter, octave in [("C", 0.0, 4), ("F", -1.0, 3), ("G", 1.0, 5)]:
        u = note_to_units(letter, alter, octave, 100)
        midi = chromatic_midi_float(letter, alter, octave)
        assert u == pytest.approx(midi)


def test_deterministic_shuffle_reproduces_metrics():
    notes = _CHROMATIC_STACK
    rng = random.Random(42)
    order = list(notes)
    rng.shuffle(order)
    m1 = _metrics(order)
    rng = random.Random(42)
    order2 = list(notes)
    rng.shuffle(order2)
    m2 = _metrics(order2)
    assert m1["H"] == pytest.approx(m2["H"])
