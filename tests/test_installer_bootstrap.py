"""Smoke tests for autonomous installer bootstrap (no download)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / "installers" / "common" / "bootstrap.py"


def test_bootstrap_doctor_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(BOOTSTRAP), "doctor"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    assert "Project root:" in proc.stdout
