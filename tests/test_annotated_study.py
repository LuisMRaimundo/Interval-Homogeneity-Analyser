"""Annotated manifest pilot study."""

from pathlib import Path

from iav.annotated_study import load_manifest, run_annotated_study

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "examples" / "annotated_corpus" / "manifest.json"


def test_annotated_manifest_loads():
    cases = load_manifest(MANIFEST)
    assert len(cases) >= 3


def test_annotated_study_runs(tmp_path):
    rows = run_annotated_study(MANIFEST, tmp_path / "out")
    assert len(rows) >= 3
    assert all("headline_H" in r or "error" in r for r in rows)
