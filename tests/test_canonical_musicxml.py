"""Frozen metrics for canonical MusicXML scores."""

from pathlib import Path

import pytest

from iav.canonical_musicxml import load_canonical_musicxml, verify_musicxml_entry

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def musicxml_canonical():
    return load_canonical_musicxml()


@pytest.mark.parametrize(
    "entry_id",
    ["major_triad", "minor_triad", "chromatic_cluster", "quartal_stack", "diminished_seventh"],
)
def test_canonical_musicxml_metrics(musicxml_canonical, entry_id: str):
    verify_musicxml_entry(musicxml_canonical[entry_id])


def test_chromatic_musicxml_chain_dominates_pair(musicxml_canonical):
    entry = musicxml_canonical["chromatic_cluster"]
    from iav.canonical_musicxml import analyze_musicxml_file

    m = analyze_musicxml_file(entry.xml_path)
    assert m["chain_score"] >= 0.95
    assert m["chain_score"] > m["pair_score"]
