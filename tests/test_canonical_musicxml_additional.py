"""Focused tests for ``iav.canonical_musicxml`` validation branches."""

from __future__ import annotations

from pathlib import Path

import pytest

from iav.canonical_musicxml import analyze_musicxml_file


def _dummy_xml_path(tmp_path: Path, name: str = "case.musicxml") -> Path:
    path = tmp_path / name
    path.write_bytes(b"<score-partwise/>")
    return path


def test_analyze_musicxml_file_raises_when_notes_skipped(tmp_path, monkeypatch):
    xml_path = _dummy_xml_path(tmp_path)

    def fake_parse(_data):
        return [("C", 0.0, 4), ("E", 0.0, 4)], 1

    monkeypatch.setattr("iav.canonical_musicxml.parse_musicxml_bytes", fake_parse)

    with pytest.raises(ValueError, match="skipped") as excinfo:
        analyze_musicxml_file(xml_path)

    assert str(xml_path) in str(excinfo.value)


def test_analyze_musicxml_file_raises_when_fewer_than_two_notes(tmp_path, monkeypatch):
    xml_path = _dummy_xml_path(tmp_path, "solo.musicxml")

    def fake_parse(_data):
        return [("C", 0.0, 4)], 0

    monkeypatch.setattr("iav.canonical_musicxml.parse_musicxml_bytes", fake_parse)

    with pytest.raises(ValueError, match="fewer than 2 notes") as excinfo:
        analyze_musicxml_file(xml_path)

    assert str(xml_path) in str(excinfo.value)


def test_analyze_musicxml_file_valid_dyad_returns_metrics(tmp_path, monkeypatch):
    xml_path = _dummy_xml_path(tmp_path, "dyad.musicxml")

    def fake_parse(_data):
        return [("C", 0.0, 4), ("G", 0.0, 4)], 0

    monkeypatch.setattr("iav.canonical_musicxml.parse_musicxml_bytes", fake_parse)

    result = analyze_musicxml_file(xml_path)

    assert "pair_score" in result
    assert "chain_score" in result
    assert "H_headline_pairwise" in result
    assert result["pair_score"] == pytest.approx(1.0)
