"""Focused tests for ``iav.canonical_corpus`` helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from iav.canonical_corpus import (
    _assert_close,
    _corpus_path,
    bundled_corpus_resource,
    export_corpus_json,
)


def test_assert_close_within_tolerance_passes():
    _assert_close(1.0, 1.0005, 0.01, "pair_score", "dyad_perfect_fifth")


def test_assert_close_outside_tolerance_raises():
    with pytest.raises(AssertionError) as excinfo:
        _assert_close(0.5, 0.9, 0.01, "pair_score", "dyad_perfect_fifth")

    message = str(excinfo.value)
    assert "dyad_perfect_fifth.pair_score" in message
    assert "got 0.500000" in message
    assert "expected 0.900000" in message
    assert "tol=0.01" in message


def test_bundled_corpus_resource_returns_package_resource_id():
    assert bundled_corpus_resource() == "iav.data:canonical_sonorities.json"


def test_export_corpus_json_writes_bundled_corpus(tmp_path: Path):
    output_path = tmp_path / "exported_canonical_sonorities.json"

    export_corpus_json(output_path)

    assert output_path.is_file()
    text = output_path.read_text(encoding="utf-8")
    assert text.strip()

    exported = json.loads(text)
    bundled = json.loads(_corpus_path().read_text(encoding="utf-8"))

    assert set(exported) >= {"schema_version", "edo", "bin_cents", "sonorities"}
    assert exported["schema_version"] == bundled["schema_version"]
    assert exported["sonorities"].keys() == bundled["sonorities"].keys()
