"""Regression: every MusicXML under validation/ must parse without crashing."""

from __future__ import annotations

import pathlib
from typing import Iterator

import pytest

from analysis_core import (
    parse_musicxml_bytes,
    parse_musicxml_sounding_verticalities_bytes,
    parse_musicxml_verticalities_bytes,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _all_validation_xml() -> Iterator[pathlib.Path]:
    for sub in ("fixtures", "corpus"):
        d = ROOT / "validation" / sub
        if not d.is_dir():
            continue
        yield from sorted(d.glob("*.xml"))


_XML_PATHS = list(_all_validation_xml())


@pytest.mark.parametrize("path", _XML_PATHS, ids=lambda p: p.name)
def test_parse_musicxml_bytes_smoke(path: pathlib.Path):
    data = path.read_bytes()
    notes, skipped = parse_musicxml_bytes(data)
    assert isinstance(notes, list)
    assert skipped >= 0


@pytest.mark.parametrize("path", _XML_PATHS, ids=lambda p: p.name)
def test_parse_verticalities_smoke(path: pathlib.Path):
    data = path.read_bytes()
    slices, skipped = parse_musicxml_verticalities_bytes(data, include_grace=True, include_cue=True)
    assert isinstance(slices, list)
    assert skipped >= 0
    for s in slices:
        assert "time" in s and "notes" in s
        assert isinstance(s["notes"], list)


@pytest.mark.parametrize("path", _XML_PATHS, ids=lambda p: p.name)
def test_parse_sounding_verticalities_smoke(path: pathlib.Path):
    data = path.read_bytes()
    slices, skipped = parse_musicxml_sounding_verticalities_bytes(data)
    assert isinstance(slices, list)
    assert skipped >= 0
    for s in slices:
        assert "start" in s and "end" in s and "notes" in s


def test_corpus_multi_voice_extracts_two_pitches():
    path = ROOT / "validation" / "corpus" / "multi_voice_same_measure.xml"
    notes, _ = parse_musicxml_bytes(path.read_bytes())
    letters = {n[0] for n in notes}
    assert letters == {"C", "E"}


def test_corpus_double_flat_pitch_height():
    path = ROOT / "validation" / "corpus" / "double_flat_explicit.xml"
    notes, _ = parse_musicxml_bytes(path.read_bytes())
    assert len(notes) == 1
    letter, alter, octave = notes[0]
    assert letter == "B"
    assert abs(float(alter) - (-2.0)) < 1e-9
    assert octave == 3
