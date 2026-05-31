"""Canonical MusicXML regression bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from iav.canonical_corpus import analyze_sonority, verify_sonority_metrics
from iav.musicxml_io import parse_musicxml_bytes

_BUNDLE_PATH = Path(__file__).resolve().parent / "data" / "canonical_musicxml.json"
_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class MusicXmlCanonicalEntry:
    entry_id: str
    xml_path: Path
    expected: Mapping[str, Any]


def load_canonical_musicxml(path: Path | None = None) -> Dict[str, MusicXmlCanonicalEntry]:
    p = path or _BUNDLE_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    out: Dict[str, MusicXmlCanonicalEntry] = {}
    for eid, block in raw["entries"].items():
        rel = block["xml_file"]
        out[eid] = MusicXmlCanonicalEntry(
            entry_id=eid,
            xml_path=_ROOT / rel,
            expected=block["expected"],
        )
    return out


def analyze_musicxml_file(xml_path: Path, *, hybrid_alpha: float = 0.6) -> Dict[str, Any]:
    notes, skipped = parse_musicxml_bytes(xml_path.read_bytes())
    if skipped:
        raise ValueError(f"skipped {skipped} notes in {xml_path}")
    if len(notes) < 2:
        raise ValueError(f"fewer than 2 notes in {xml_path}")
    return analyze_sonority(notes, hybrid_alpha=hybrid_alpha, bin_cents=100)


def verify_musicxml_entry(entry: MusicXmlCanonicalEntry, tolerance: float = 1e-3) -> None:
    computed = analyze_musicxml_file(entry.xml_path)
    verify_sonority_metrics(computed, entry.expected, entry.entry_id, tolerance=tolerance)
    if "note_count" in entry.expected:
        notes, _ = parse_musicxml_bytes(entry.xml_path.read_bytes())
        assert len(notes) == int(entry.expected["note_count"]), entry.entry_id
