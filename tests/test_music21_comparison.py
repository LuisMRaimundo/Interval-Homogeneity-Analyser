"""Compare 12-TET interval vectors with music21 when installed (optional)."""

from __future__ import annotations

import pytest

from iav.canonical_corpus import load_canonical_corpus
from iav.interval_analysis_core import interval_vector_12tet, pitch_classes_12tet_unique


def _music21_iv(pcs: list[int]) -> list[int]:
    pytest.importorskip("music21")
    from music21.chord import Chord
    from music21.pitch import Pitch

    ch = Chord([Pitch(midi=60 + pc) for pc in sorted(set(pcs))])
    return list(ch.intervalVector)


@pytest.mark.parametrize(
    "sonority_id",
    [
        "major_triad_closed",
        "minor_triad_closed",
        "diminished_seventh",
        "augmented_triad",
    ],
)
def test_interval_vector_matches_music21(sonority_id: str):
    pytest.importorskip("music21")
    _, specs = load_canonical_corpus()
    spec = specs[sonority_id]
    pcs = pitch_classes_12tet_unique(spec.notes)
    assert pcs is not None
    ours = interval_vector_12tet(pcs)
    m21 = _music21_iv(pcs)
    assert ours == m21, f"{sonority_id}: iav {ours} vs music21 {m21}"
