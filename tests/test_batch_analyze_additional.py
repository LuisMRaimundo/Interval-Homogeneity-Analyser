"""Focused tests for ``iav.batch_analyze``."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from iav.analysis_enums import MusicXmlImportMode
from iav.batch_analyze import (
    BatchConfig,
    _analyze_one,
    _load_notes_from_path,
    run_batch,
    run_canonical_verification,
)


def _batch_cfg(tmp_path: Path, **kwargs) -> BatchConfig:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    return BatchConfig(input_dir=input_dir, output_dir=output_dir, **kwargs)


@pytest.mark.parametrize("suffix", [".xml", ".musicxml"])
def test_load_notes_from_path_xml_uses_aggregate_mode(tmp_path, monkeypatch, suffix):
    cfg = _batch_cfg(tmp_path)
    xml_path = cfg.input_dir / f"score{suffix}"
    xml_path.write_bytes(b"<score-partwise/>")

    expected_notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    captured: list[tuple[bytes, MusicXmlImportMode]] = []

    def fake_parse(data, mode, **kwargs):
        captured.append((data, mode))
        return expected_notes, 0

    monkeypatch.setattr("iav.batch_analyze.parse_musicxml_upload", fake_parse)

    notes = _load_notes_from_path(xml_path, cfg)

    assert notes == expected_notes
    assert captured == [(b"<score-partwise/>", MusicXmlImportMode.AGGREGATE)]


def test_load_notes_from_path_mxl_reads_embedded_xml(tmp_path, monkeypatch):
    cfg = _batch_cfg(tmp_path)
    mxl_path = cfg.input_dir / "score.mxl"
    xml_bytes = b"<score-partwise version='3.0'/>"

    with zipfile.ZipFile(mxl_path, "w") as zf:
        zf.writestr("readme.txt", "mxl container metadata only")
        zf.writestr("score.musicxml", xml_bytes)

    captured: list[bytes] = []

    def fake_parse(data, mode, **kwargs):
        captured.append(data)
        return [("C", 0.0, 4), ("G", 0.0, 4)], 0

    monkeypatch.setattr("iav.batch_analyze.parse_musicxml_upload", fake_parse)

    notes = _load_notes_from_path(mxl_path, cfg)

    assert notes == [("C", 0.0, 4), ("G", 0.0, 4)]
    assert captured == [xml_bytes]


def test_load_notes_from_path_mxl_without_xml_raises(tmp_path):
    cfg = _batch_cfg(tmp_path)
    mxl_path = cfg.input_dir / "empty.mxl"
    with zipfile.ZipFile(mxl_path, "w") as zf:
        zf.writestr("readme.txt", "no score here")

    with pytest.raises(ValueError, match="No XML inside MXL"):
        _load_notes_from_path(mxl_path, cfg)


def test_load_notes_from_path_unsupported_extension_raises(tmp_path):
    cfg = _batch_cfg(tmp_path)
    txt_path = cfg.input_dir / "notes.txt"
    txt_path.write_text("not supported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported input"):
        _load_notes_from_path(txt_path, cfg)


def test_analyze_one_fewer_than_two_notes():
    cfg = BatchConfig(input_dir=Path("."), output_dir=Path("."))
    row = _analyze_one("solo", [("C", 0.0, 4)], cfg)

    assert row == {
        "source_id": "solo",
        "error": "fewer than 2 notes",
        "note_count": 1,
    }


def test_analyze_one_valid_dyad_returns_metric_keys():
    cfg = BatchConfig(input_dir=Path("."), output_dir=Path("."))
    row = _analyze_one("dyad", [("C", 0.0, 4), ("G", 0.0, 4)], cfg)

    assert row["source_id"] == "dyad"
    assert row["note_count"] == 2
    assert "headline_H" in row
    assert "H_label" in row
    assert "classification" in row
    assert "pair_score" in row
    assert "error" not in row


def test_run_batch_catches_load_exception(tmp_path, monkeypatch):
    cfg = _batch_cfg(tmp_path)
    (cfg.input_dir / "case.json").write_text(
        json.dumps({"notes": [["C", 0.0, 4], ["E", 0.0, 4]]}),
        encoding="utf-8",
    )

    def boom(path, batch_cfg):
        raise RuntimeError("load failed")

    monkeypatch.setattr("iav.batch_analyze._load_notes_from_path", boom)

    result = run_batch(cfg)

    assert result["results"][0] == {"source_id": "case", "error": "load failed"}


def test_run_batch_catches_processing_exception(tmp_path, monkeypatch):
    cfg = _batch_cfg(tmp_path)
    (cfg.input_dir / "case.json").write_text(
        json.dumps({"notes": [["C", 0.0, 4], ["E", 0.0, 4]]}),
        encoding="utf-8",
    )

    def boom(source_id, notes, batch_cfg):
        raise RuntimeError("analysis exploded")

    monkeypatch.setattr("iav.batch_analyze._analyze_one", boom)

    result = run_batch(cfg)

    assert len(result["results"]) == 1
    assert result["results"][0]["source_id"] == "case"
    assert result["results"][0]["error"] == "analysis exploded"
    assert (cfg.output_dir / "results.json").is_file()
    assert (cfg.output_dir / "results.csv").is_file()


def test_run_batch_writes_output_files_for_success_and_error(tmp_path, monkeypatch):
    cfg = _batch_cfg(tmp_path)
    (cfg.input_dir / "good.json").write_text(
        json.dumps({"notes": [["C", 0.0, 4], ["G", 0.0, 4]]}),
        encoding="utf-8",
    )
    (cfg.input_dir / "bad.json").write_text(
        json.dumps({"notes": [["C", 0.0, 4]]}),
        encoding="utf-8",
    )

    result = run_batch(cfg)

    assert len(result["results"]) == 2
    csv_text = (cfg.output_dir / "results.csv").read_text(encoding="utf-8")
    assert "source_id" in csv_text
    assert "good" in csv_text
    assert "bad" in csv_text
    assert "fewer than 2 notes" in csv_text

    saved = json.loads((cfg.output_dir / "results.json").read_text(encoding="utf-8"))
    by_id = {row["source_id"]: row for row in saved["results"]}
    assert by_id["bad"]["error"] == "fewer than 2 notes"
    assert by_id["good"].get("error") is None


def test_run_canonical_verification_success_without_output_dir():
    assert run_canonical_verification(None) == 0


def test_run_canonical_verification_failure_writes_report(tmp_path, monkeypatch):
    def fail_verify(computed, expected, sonority_id, **kwargs):
        raise AssertionError(f"metric mismatch for {sonority_id}")

    monkeypatch.setattr("iav.canonical_corpus.verify_sonority_metrics", fail_verify)

    assert run_canonical_verification(tmp_path) == 1

    report = json.loads((tmp_path / "canonical_verification.json").read_text(encoding="utf-8"))
    assert report["failures"]
    assert report["results"]
    assert all(row["ok"] is False for row in report["results"])
