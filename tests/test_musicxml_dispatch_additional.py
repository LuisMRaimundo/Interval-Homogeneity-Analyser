"""Dispatch routing tests for ``iav.musicxml_io._dispatch.parse_musicxml_upload``."""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from iav.analysis_enums import MusicXmlImportMode
from iav.musicxml_io._dispatch import parse_musicxml_upload

_FILE_BYTES = b"<score-partwise/>"
_STUB_RESULT_NOTES: tuple = ([("C", 0.0, 4)], 0)
_STUB_RESULT_SLICES: tuple = ([{"time": 0.0, "notes": [("C", 0.0, 4)]}], 0)

@pytest.fixture
def parser_calls(monkeypatch: pytest.MonkeyPatch) -> List[Dict[str, Any]]:
    calls: List[Dict[str, Any]] = []

    def _make_stub(name: str, *, slices: bool):
        def _stub(*args: Any, **kwargs: Any):
            calls.append({"name": name, "args": args, "kwargs": kwargs})
            return _STUB_RESULT_SLICES if slices else _STUB_RESULT_NOTES

        return _stub

    monkeypatch.setattr(
        "iav.musicxml_io._dispatch.parse_musicxml_bytes",
        _make_stub("parse_musicxml_bytes", slices=False),
    )
    monkeypatch.setattr(
        "iav.musicxml_io._dispatch.parse_musicxml_bytes_with_sounding_transpose",
        _make_stub("parse_musicxml_bytes_with_sounding_transpose", slices=False),
    )
    monkeypatch.setattr(
        "iav.musicxml_io._dispatch.parse_musicxml_verticalities_bytes",
        _make_stub("parse_musicxml_verticalities_bytes", slices=True),
    )
    monkeypatch.setattr(
        "iav.musicxml_io._dispatch.parse_musicxml_verticalities_bytes_with_sounding_transpose",
        _make_stub(
            "parse_musicxml_verticalities_bytes_with_sounding_transpose",
            slices=True,
        ),
    )
    monkeypatch.setattr(
        "iav.musicxml_io._dispatch.parse_musicxml_sounding_verticalities_bytes",
        _make_stub("parse_musicxml_sounding_verticalities_bytes", slices=True),
    )
    monkeypatch.setattr(
        "iav.musicxml_io._dispatch.parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose",
        _make_stub(
            "parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose",
            slices=True,
        ),
    )
    return calls


def _assert_single_call(calls: List[Dict[str, Any]], expected_name: str) -> Dict[str, Any]:
    assert len(calls) == 1
    assert calls[0]["name"] == expected_name
    return calls[0]


@pytest.mark.parametrize(
    ("apply_sounding_transpose", "expected_parser"),
    [
        (False, "parse_musicxml_bytes"),
        (True, "parse_musicxml_bytes_with_sounding_transpose"),
    ],
)
def test_dispatch_aggregate_mode_routes_to_flat_parser(
    parser_calls,
    apply_sounding_transpose,
    expected_parser,
):
    result = parse_musicxml_upload(
        _FILE_BYTES,
        MusicXmlImportMode.AGGREGATE,
        include_grace=True,
        include_cue=True,
        apply_sounding_transpose=apply_sounding_transpose,
    )
    call = _assert_single_call(parser_calls, expected_parser)
    assert call["args"] == (_FILE_BYTES,)
    assert call["kwargs"] == {}
    assert result == _STUB_RESULT_NOTES


@pytest.mark.parametrize(
    ("apply_sounding_transpose", "expected_parser"),
    [
        (False, "parse_musicxml_verticalities_bytes"),
        (True, "parse_musicxml_verticalities_bytes_with_sounding_transpose"),
    ],
)
def test_dispatch_onset_verticalities_mode_routes_to_onset_parser(
    parser_calls,
    apply_sounding_transpose,
    expected_parser,
):
    result = parse_musicxml_upload(
        _FILE_BYTES,
        MusicXmlImportMode.ONSET_VERTICALITIES,
        include_grace=True,
        include_cue=False,
        apply_sounding_transpose=apply_sounding_transpose,
    )
    call = _assert_single_call(parser_calls, expected_parser)
    assert call["args"] == (_FILE_BYTES,)
    assert call["kwargs"] == {"include_grace": True, "include_cue": False}
    assert result == _STUB_RESULT_SLICES


@pytest.mark.parametrize(
    ("apply_sounding_transpose", "expected_parser"),
    [
        (False, "parse_musicxml_sounding_verticalities_bytes"),
        (True, "parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose"),
    ],
)
def test_dispatch_sounding_verticalities_mode_routes_to_sounding_parser(
    parser_calls,
    apply_sounding_transpose,
    expected_parser,
):
    result = parse_musicxml_upload(
        _FILE_BYTES,
        MusicXmlImportMode.SOUNDING_VERTICALITIES,
        include_grace=False,
        include_cue=True,
        apply_sounding_transpose=apply_sounding_transpose,
    )
    call = _assert_single_call(parser_calls, expected_parser)
    assert call["args"] == (_FILE_BYTES,)
    assert call["kwargs"] == {}
    assert result == _STUB_RESULT_SLICES


def test_dispatch_onset_verticalities_forwards_grace_and_cue_flags(parser_calls):
    parse_musicxml_upload(
        _FILE_BYTES,
        MusicXmlImportMode.ONSET_VERTICALITIES,
        include_grace=False,
        include_cue=True,
        apply_sounding_transpose=False,
    )
    call = _assert_single_call(parser_calls, "parse_musicxml_verticalities_bytes")
    assert call["kwargs"]["include_grace"] is False
    assert call["kwargs"]["include_cue"] is True


def test_dispatch_aggregate_ignores_grace_and_cue_flags(parser_calls):
    parse_musicxml_upload(
        _FILE_BYTES,
        MusicXmlImportMode.AGGREGATE,
        include_grace=True,
        include_cue=True,
        apply_sounding_transpose=False,
    )
    call = _assert_single_call(parser_calls, "parse_musicxml_bytes")
    assert "include_grace" not in call["kwargs"]
    assert "include_cue" not in call["kwargs"]


def test_dispatch_sounding_verticalities_ignores_grace_and_cue_flags(parser_calls):
    parse_musicxml_upload(
        _FILE_BYTES,
        MusicXmlImportMode.SOUNDING_VERTICALITIES,
        include_grace=True,
        include_cue=True,
        apply_sounding_transpose=False,
    )
    call = _assert_single_call(parser_calls, "parse_musicxml_sounding_verticalities_bytes")
    assert "include_grace" not in call["kwargs"]
    assert "include_cue" not in call["kwargs"]


def test_dispatch_only_three_enum_modes_exist():
    """No separate unknown-mode fallback: non-aggregate/non-sounding uses onset parsers."""
    assert set(MusicXmlImportMode) == {
        MusicXmlImportMode.AGGREGATE,
        MusicXmlImportMode.ONSET_VERTICALITIES,
        MusicXmlImportMode.SOUNDING_VERTICALITIES,
    }
