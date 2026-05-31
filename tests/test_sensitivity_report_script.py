"""Sensitivity report generator smoke test."""

from pathlib import Path

from scripts.sensitivity_report import main

ROOT = Path(__file__).resolve().parent.parent


def test_sensitivity_report_writes_files(tmp_path, monkeypatch):
    out = tmp_path / "reports"
    monkeypatch.setattr("scripts.sensitivity_report.OUT_DIR", out)
    main()
    assert (out / "sensitivity_alpha.csv").is_file()
    assert (out / "sensitivity_alpha.md").is_file()
    assert (out / "sensitivity_h_bands.csv").is_file()
