"""Batch CLI smoke tests."""

from pathlib import Path

from iav.batch_analyze import BatchConfig, run_batch, run_canonical_verification
from iav.cli import main

ROOT = Path(__file__).resolve().parent.parent


def test_run_canonical_verification_passes(tmp_path):
    assert run_canonical_verification(tmp_path) == 0
    assert (tmp_path / "canonical_verification.json").is_file()


def test_batch_on_examples_corpus(tmp_path):
    cfg = BatchConfig(
        input_dir=ROOT / "examples" / "corpus",
        output_dir=tmp_path / "out",
    )
    result = run_batch(cfg)
    assert len(result["results"]) >= 10
    assert (tmp_path / "out" / "results.csv").is_file()
    assert (tmp_path / "out" / "results.json").is_file()
    assert (tmp_path / "out" / "config_used.json").is_file()


def test_cli_verify_canonical(tmp_path):
    code = main(
        [
            "--verify-canonical",
            "-i",
            str(ROOT / "examples" / "corpus"),
            "-o",
            str(tmp_path / "ci"),
        ]
    )
    assert code == 0
