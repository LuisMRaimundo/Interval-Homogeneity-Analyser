"""Focused tests for ``iav.musicxml_io._onset_verticalities`` uncovered branches."""

from __future__ import annotations

import pytest

from iav.musicxml_io._onset_verticalities import (
    parse_musicxml_verticalities_bytes,
    parse_musicxml_verticalities_bytes_with_sounding_transpose,
)


def _score(body: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<score-partwise version="3.1"><part id="P1">{body}</part></score-partwise>'
    ).encode("utf-8")


def _measure(inner: str, *, attributes: str = "<divisions>1</divisions>") -> str:
    return f'<measure number="1"><attributes>{attributes}</attributes>{inner}</measure>'


def _note(step: str, octave: int, *, duration: int = 1) -> str:
    return (
        f"<note><pitch><step>{step}</step><octave>{octave}</octave></pitch>"
        f"<duration>{duration}</duration></note>"
    )


def test_parse_onset_verticalities_when_get_musicxml_bytes_none(monkeypatch):
    monkeypatch.setattr(
        "iav.musicxml_io._onset_verticalities.get_musicxml_bytes",
        lambda _b: None,
    )
    slices, skipped = parse_musicxml_verticalities_bytes(
        b"ignored",
        include_grace=False,
        include_cue=False,
    )
    assert slices == []
    assert skipped == 0


def test_transpose_wrapper_passes_apply_musicxml_transpose_true(monkeypatch):
    captured: dict = {}

    def _capture_impl(file_bytes, include_grace, include_cue, *, apply_musicxml_transpose):
        captured["file_bytes"] = file_bytes
        captured["include_grace"] = include_grace
        captured["include_cue"] = include_cue
        captured["apply_musicxml_transpose"] = apply_musicxml_transpose
        return [], 0

    monkeypatch.setattr(
        "iav.musicxml_io._onset_verticalities._parse_musicxml_verticalities_impl",
        _capture_impl,
    )
    payload = b"<score-partwise/>"
    parse_musicxml_verticalities_bytes_with_sounding_transpose(
        payload,
        include_grace=True,
        include_cue=False,
    )
    assert captured == {
        "file_bytes": payload,
        "include_grace": True,
        "include_cue": False,
        "apply_musicxml_transpose": True,
    }


def test_written_vs_sounding_onset_verticalities_differ_with_transpose():
    body = _measure(
        _note("D", 4),
        attributes="<divisions>1</divisions><transpose><chromatic>-2</chromatic></transpose>",
    )
    xml = _score(body)
    written, skipped_w = parse_musicxml_verticalities_bytes(
        xml,
        include_grace=False,
        include_cue=False,
    )
    sounding, skipped_s = parse_musicxml_verticalities_bytes_with_sounding_transpose(
        xml,
        include_grace=False,
        include_cue=False,
    )
    assert skipped_w == 0
    assert skipped_s == 0
    assert len(written) == 1
    assert len(sounding) == 1
    assert written[0]["time"] == pytest.approx(0.0)
    assert sounding[0]["time"] == pytest.approx(0.0)
    assert written[0]["notes"] == [("D", 0.0, 4)]
    assert sounding[0]["notes"] == [("C", 0.0, 4)]


def test_non_transposed_baseline_matches_written_pitch_only():
    body = _measure(_note("E", 4))
    xml = _score(body)
    written, _ = parse_musicxml_verticalities_bytes(xml, include_grace=False, include_cue=False)
    sounding, _ = parse_musicxml_verticalities_bytes_with_sounding_transpose(
        xml,
        include_grace=False,
        include_cue=False,
    )
    assert written == sounding == [{"time": 0.0, "notes": [("E", 0.0, 4)]}]
