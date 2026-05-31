#!/usr/bin/env python3
"""Run examples/annotated_corpus/manifest.json pilot study."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iav.annotated_study import run_annotated_study

MANIFEST = ROOT / "examples" / "annotated_corpus" / "manifest.json"
OUT = ROOT / "docs" / "reports" / "annotated_pilot"


def main() -> int:
    rows = run_annotated_study(MANIFEST, OUT)
    mismatches = [r for r in rows if r.get("texture_match") is False]
    if mismatches:
        print(f"WARNING: {len(mismatches)} texture mismatches (pilot labels)")
    print(f"Wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
