#!/usr/bin/env python3
"""Write validation/canonical/*.xml and iav/data/canonical_musicxml.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iav.canonical_corpus import analyze_sonority
from iav.musicxml_io import parse_musicxml_bytes

CANON_DIR = ROOT / "validation" / "canonical"
OUT_JSON = ROOT / "iav" / "data" / "canonical_musicxml.json"

_SCORES: dict[str, list[tuple[str, int, int]]] = {
    "major_triad": [("C", 0, 4), ("E", 0, 4), ("G", 0, 4)],
    "minor_triad": [("C", 0, 4), ("E", -1, 4), ("G", 0, 4)],
    "chromatic_cluster": [
        ("C", 0, 4),
        ("C", 1, 4),
        ("D", 0, 4),
        ("D", 1, 4),
        ("E", 0, 4),
        ("F", 0, 4),
    ],
    "quartal_stack": [("C", 0, 4), ("F", 0, 4), ("B", -1, 4), ("E", -1, 5)],
    "diminished_seventh": [("C", 0, 4), ("E", -1, 4), ("G", -1, 4), ("B", -1, 4)],
}


def _pitch_xml(step: str, alter: int, octave: int) -> str:
    if alter == 0:
        return f"<pitch><step>{step}</step><octave>{octave}</octave></pitch>"
    return (
        f"<pitch><step>{step}</step><alter>{alter}</alter>"
        f"<octave>{octave}</octave></pitch>"
    )


def _write_score(score_id: str, notes: list[tuple[str, int, int]]) -> Path:
    note_lines = [
        f"      <note>{_pitch_xml(s, a, o)}<duration>1</duration></note>" for s, a, o in notes
    ]
    attrs = "      <attributes><divisions>1</divisions></attributes>"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<score-partwise version="3.1">',
        "  <part-list>",
        '    <score-part id="P1"><part-name>Canonical</part-name></score-part>',
        "  </part-list>",
        '  <part id="P1">',
        "    <measure number=\"1\">",
        attrs,
        *note_lines,
        "    </measure>",
        "  </part>",
        "</score-partwise>",
        "",
    ]
    path = CANON_DIR / f"{score_id}.xml"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    CANON_DIR.mkdir(parents=True, exist_ok=True)
    bundle: dict = {
        "schema_version": 1,
        "edo": 12,
        "bin_cents": 100,
        "homogeneity_method": "dominance",
        "hybrid_alpha": 0.6,
        "entries": {},
    }
    for score_id, note_spec in _SCORES.items():
        xml_path = _write_score(score_id, note_spec)
        notes, skipped = parse_musicxml_bytes(xml_path.read_bytes())
        assert skipped == 0, score_id
        metrics = analyze_sonority(notes, hybrid_alpha=0.6, bin_cents=100)
        for k, v in list(metrics.items()):
            if isinstance(v, float):
                metrics[k] = round(v, 4)
        constraints: dict = {}
        if score_id == "chromatic_cluster":
            constraints = {
                "chain_score_min": 0.95,
                "pair_score_max": 0.99,
                "chain_gt_pair": True,
            }
        elif score_id == "quartal_stack":
            constraints = {"chain_score_min": 0.95}
        bundle["entries"][score_id] = {
            "xml_file": f"validation/canonical/{score_id}.xml",
            "expected": {**metrics, "constraints": constraints, "note_count": len(notes)},
        }
    OUT_JSON.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(bundle['entries'])} entries to {OUT_JSON}")


if __name__ == "__main__":
    main()
