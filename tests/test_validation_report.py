"""Tests for scripts/validation_report.py (synthetic fixture)."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_CSV = Path(__file__).resolve().parent / "fixtures" / "validation_annotations_minimal.csv"
SCRIPT = ROOT / "scripts" / "validation_report.py"


@pytest.fixture(scope="module")
def batch_metrics_path(tmp_path_factory):
    import tempfile

    out = tempfile.mkdtemp()
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "analyze_corpus.py"),
            "-i",
            str(ROOT / "examples" / "corpus"),
            "-o",
            out,
        ],
        check=True,
        cwd=str(ROOT),
    )
    return Path(out) / "results.json"


def _load_validation_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("validation_report", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_validation_summary_without_metrics():
    mod = _load_validation_module()
    rows = mod._load_annotations(FIXTURE_CSV)
    summary = mod.build_validation_summary(rows, {})
    assert summary["n_annotations"] == 4
    assert summary["cohen_kappa_global_two_raters"] is not None
    assert "confusion_matrix_human_rows_tool_cols" in summary


def test_validation_report_cli_writes_outputs(tmp_path, batch_metrics_path):
    out_dir = tmp_path / "val_out"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(FIXTURE_CSV),
            "--metrics",
            str(batch_metrics_path),
            "--output",
            str(out_dir),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.returncode == 0
    assert (out_dir / "validation_summary.json").is_file()
    assert (out_dir / "validation_summary.csv").is_file()
    payload = json.loads((out_dir / "validation_summary.json").read_text(encoding="utf-8"))
    assert payload["n_cases"] >= 3
    assert "joined_rows" in payload
    with (out_dir / "validation_summary.csv").open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames
        assert sum(1 for _ in reader) == payload["n_annotations"]
