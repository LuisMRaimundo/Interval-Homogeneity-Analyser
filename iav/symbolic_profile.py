"""
Intervallic supplements: reference sonority fingerprints and optional mod-12 ic evenness.
Not registral dispersion (that belongs in a separate tool).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from iav.interval_analysis_core._edo_labels import (
    intervals_for_notes,
    parse_note_name,
)
from iav.note_types import NoteTuple
from iav.set_class_12tet import interval_vector_12tet, pitch_classes_12tet_unique

_REFERENCE_PATH = Path(__file__).resolve().parent / "data" / "reference_sonorities.json"


@dataclass(frozen=True)
class IntervallicProfile:
    """Optional intervallic context beyond headline H (not registral layout metrics)."""

    ic_evenness: Optional[float]
    ic_cardinality: Optional[int]
    reference_comparisons: Tuple[Tuple[str, str, float], ...]


def _catalog_note_tuple(raw: Sequence[Any]) -> NoteTuple:
    name = str(raw[0]).strip()
    octave = int(raw[2])
    if len(name) > 1:
        parsed = parse_note_name(name)
        if parsed is not None:
            return parsed[0], parsed[1], octave
    return name[0].upper(), float(raw[1]), octave


def _load_reference_catalog() -> Dict[str, Any]:
    if not _REFERENCE_PATH.is_file():
        return {}
    return json.loads(_REFERENCE_PATH.read_text(encoding="utf-8"))


def reference_catalog() -> Dict[str, Dict[str, Any]]:
    raw = _load_reference_catalog()
    return {k: {"id": k, **v} for k, v in raw.items()}


def entropy_evenness_counts(counts: Mapping[Any, int]) -> float:
    if not counts:
        return 0.0
    total = sum(counts.values())
    vals = list(counts.values())
    if len(vals) <= 1 or total <= 0:
        return 0.0
    ent = 0.0
    for c in vals:
        p = c / total
        if p > 0:
            ent -= p * math.log(p)
    mx = math.log(len(vals))
    return 0.0 if mx <= 0 else ent / mx


def ic_evenness_from_notes(notes: Sequence[NoteTuple]) -> Tuple[Optional[float], Optional[int]]:
    pcs = pitch_classes_12tet_unique(notes)
    if pcs is None or len(pcs) < 2:
        return None, len(pcs) if pcs else None
    iv = interval_vector_12tet(pcs)
    ic_counts = {i + 1: iv[i] for i in range(6) if iv[i] > 0}
    return entropy_evenness_counts(ic_counts), len(pcs)


def normalized_distance_histogram(
    distance_counts: Mapping[int, int],
) -> Dict[int, float]:
    total = sum(distance_counts.values())
    if total <= 0:
        return {}
    return {int(k): v / total for k, v in distance_counts.items()}


def histogram_l1_distance(a: Mapping[int, float], b: Mapping[int, float]) -> float:
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def compare_to_references(
    distance_counts: Mapping[int, int],
    *,
    edo: int,
    top_n: int = 4,
) -> Tuple[Tuple[str, str, float], ...]:
    catalog = _load_reference_catalog()
    if not catalog or not distance_counts:
        return ()
    target = normalized_distance_histogram(distance_counts)
    ref_bin = int(round(1200 / edo))
    scored: List[Tuple[str, str, float]] = []
    for ref_id, spec in catalog.items():
        if int(spec.get("edo", 12)) != edo:
            continue
        notes = [_catalog_note_tuple(n) for n in spec.get("notes", [])]
        if len(notes) < 2:
            continue
        _, ref_dist = intervals_for_notes(notes, ref_bin)
        d = histogram_l1_distance(target, normalized_distance_histogram(ref_dist))
        scored.append((ref_id, str(spec.get("label", ref_id)), d))
    scored.sort(key=lambda x: x[2])
    return tuple(scored[:top_n])


def intervallic_profile_for_notes(
    notes: Sequence[NoteTuple],
    *,
    edo: int,
    distance_counts: Mapping[int, int],
) -> IntervallicProfile:
    ic_even, ic_card = ic_evenness_from_notes(notes)
    return IntervallicProfile(
        ic_evenness=ic_even,
        ic_cardinality=ic_card,
        reference_comparisons=compare_to_references(distance_counts, edo=edo),
    )


# Backward-compatible aliases (older imports / docs)
SymbolicProfile = IntervallicProfile
symbolic_profile_for_notes = intervallic_profile_for_notes


def _headline_h_column(row: Mapping[str, Any]) -> Optional[str]:
    if "H (consensus)" in row:
        return "H (consensus)"
    for k in row:
        if k.startswith("H ("):
            return k
    if "H" in row:
        return "H"
    return None


def passage_delta_rows(summary_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Append ΔH between consecutive slices (intervallic homogeneity along score time)."""
    if not summary_rows:
        return summary_rows
    if len(summary_rows) == 1:
        only = dict(summary_rows[0])
        only["ΔH (prev slice)"] = None
        return [only]
    out: List[Dict[str, Any]] = []
    prev: Optional[Dict[str, Any]] = None
    for row in summary_rows:
        new_row = dict(row)
        if prev is not None:
            h_key = _headline_h_column(row) or "H"
            try:
                dh = float(row.get(h_key, 0)) - float(prev.get(h_key, 0))
            except (TypeError, ValueError):
                dh = None
            new_row["ΔH (prev slice)"] = round(dh, 3) if dh is not None else None
        else:
            new_row["ΔH (prev slice)"] = None
        out.append(new_row)
        prev = row
    return out


def slice_intervallic_columns(
    slice_notes: Sequence[NoteTuple],
    metrics: Mapping[str, Any],
    bin_cents: int,
) -> Dict[str, Any]:
    profile = intervallic_profile_for_notes(
        slice_notes,
        edo=int(round(1200 / bin_cents)),
        distance_counts=metrics["distance_counts"],
    )
    cols: Dict[str, Any] = {}
    if profile.ic_cardinality is not None:
        cols["PC cardinality"] = profile.ic_cardinality
    if profile.ic_evenness is not None:
        cols["IC evenness (mod 12)"] = round(profile.ic_evenness, 3)
    return cols


# Legacy name
slice_symbolic_columns = slice_intervallic_columns
