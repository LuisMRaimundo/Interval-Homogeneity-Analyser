"""Focused tests for ``iav.cli``."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from iav.analysis_enums import IntervallicHeadlineMode
from iav.cli import main


def test_verify_canonical_missing_input_returns_zero_without_batch(tmp_path, monkeypatch):
    output_dir = tmp_path / "verify_out"
    missing_input = tmp_path / "no_such_input_dir"

    verify_called: list[Path] = []

    def fake_verify(output_dir_arg):
        verify_called.append(output_dir_arg)
        return 0

    batch_called: list[object] = []

    def fake_batch(_cfg):
        batch_called.append(True)

    monkeypatch.setattr("iav.cli.run_canonical_verification", fake_verify)
    monkeypatch.setattr("iav.cli.run_batch", fake_batch)

    code = main(
        [
            "--verify-canonical",
            "-i",
            str(missing_input),
            "-o",
            str(output_dir),
        ]
    )

    assert code == 0
    assert verify_called == [output_dir]
    assert batch_called == []


@pytest.mark.parametrize(
    "input_path_factory",
    [
        lambda tmp: tmp / "missing_input_dir",
        lambda tmp: _write_file(tmp / "notes.txt", "not a directory"),
    ],
)
def test_main_returns_two_when_input_not_directory(
    tmp_path, capsys, input_path_factory
):
    input_path = input_path_factory(tmp_path)
    output_path = tmp_path / "output"

    code = main(["-i", str(input_path), "-o", str(output_path)])

    assert code == 2
    captured = capsys.readouterr()
    assert "Input not found:" in captured.err
    assert str(input_path) in captured.err


def test_main_maps_arguments_to_batch_config(tmp_path, monkeypatch):
    input_dir = tmp_path / "corpus_in"
    input_dir.mkdir()
    output_dir = tmp_path / "corpus_out"

    captured: list[object] = []

    def fake_run_batch(cfg):
        captured.append(cfg)

    monkeypatch.setattr("iav.cli.run_batch", fake_run_batch)

    code = main(
        [
            "-i",
            str(input_dir),
            "-o",
            str(output_dir),
            "--edo",
            "24",
            "--headline",
            "hybrid_intervallic_homogeneity",
            "--method",
            "entropy",
            "--alpha",
            "0.42",
            "--auto-alpha",
            "--k-auto",
            "6",
            "--no-dedupe",
            "--sounding-transpose",
        ]
    )

    assert code == 0
    assert len(captured) == 1
    cfg = captured[0]
    assert cfg.input_dir == input_dir
    assert cfg.output_dir == output_dir
    assert cfg.edo == 24
    assert cfg.headline_mode == IntervallicHeadlineMode.HYBRID
    assert cfg.homogeneity_method == "entropy"
    assert cfg.hybrid_alpha_base == pytest.approx(0.42)
    assert cfg.auto_alpha is True
    assert cfg.k_auto == 6
    assert cfg.remove_duplicates is False
    assert cfg.apply_sounding_transpose is True


def _write_file(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_cli_module_main_entrypoint(tmp_path, monkeypatch):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    output_dir = tmp_path / "out"

    monkeypatch.setattr(sys, "argv", ["iav-analyze", "-i", str(input_dir), "-o", str(output_dir)])
    monkeypatch.setattr("iav.cli.run_batch", lambda _cfg: {"results": []})

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("iav.cli", run_name="__main__")

    assert excinfo.value.code == 0
