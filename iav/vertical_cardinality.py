"""
Symbolic vertical cardinality over score time (not acoustic density).

Counts notated pitch events / pitch units / pitch classes per vertical slice.
"""

from __future__ import annotations

import json
import statistics
from typing import Any, Dict, List, Mapping, Optional, Sequence

from iav.analysis_enums import MusicXmlImportMode
from iav.charts import parse_slice_time_quarters
from iav.interval_analysis_core import dedupe_notes_by_midi, note_to_units
from iav.note_types import NoteTuple
from iav.set_class_12tet import pitch_classes_12tet_unique

VERTICAL_CARDINALITY_SCHEMA_VERSION = "1.0"

DEFINITIONS: Dict[str, str] = {
    "vertical_note_count": (
        "Number of notes/events active in the vertical slice after the current deduplication setting."
    ),
    "vertical_unique_pitch_count": (
        "Number of distinct pitch units active in the vertical slice, when available."
    ),
    "vertical_pitch_class_cardinality": (
        "Number of distinct pitch classes active in the vertical slice, when available."
    ),
}


def vertical_cardinality_for_notes(
    notes: Sequence[NoteTuple],
    *,
    bin_cents: int,
    edo: int,
) -> Dict[str, Optional[int]]:
    """
    Cardinality metrics for one vertical slice (after caller-applied dedupe).
    """
    n_events = len(notes)
    if n_events == 0:
        return {
            "vertical_note_count": 0,
            "vertical_unique_pitch_count": 0,
            "vertical_pitch_class_cardinality": 0 if edo == 12 else None,
        }
    units = {note_to_units(*n, bin_cents=bin_cents) for n in notes}
    unique_pitch = len(units)
    pc_card: Optional[int]
    if edo == 12:
        pcs = pitch_classes_12tet_unique(notes)
        pc_card = len(pcs) if pcs is not None else None
    else:
        pc_card = None
    return {
        "vertical_note_count": n_events,
        "vertical_unique_pitch_count": unique_pitch,
        "vertical_pitch_class_cardinality": pc_card,
    }


def vertical_cardinality_from_summary_row(
    row: Mapping[str, Any],
    *,
    bin_cents: int,
    edo: int,
) -> Dict[str, Optional[int]]:
    """
    Recover cardinality from a slice-summary row (``Notes`` must match CSV when present).

    ``vertical_pitch_class_cardinality`` is taken only from an explicit ``PC cardinality``
    column; it is never inferred from unique pitch count (octave duplicates break that identity).
    """
    notes_raw = row.get("Notes")
    if notes_raw is None or notes_raw == "":
        vnc: Optional[int] = None
    else:
        try:
            vnc = int(notes_raw)
        except (TypeError, ValueError):
            vnc = None

    unique_raw = row.get("Unique pitches")
    if unique_raw is None or unique_raw == "":
        vup: Optional[int] = vnc if vnc is not None else None
    else:
        try:
            vup = int(unique_raw)
        except (TypeError, ValueError):
            vup = None

    pc_raw = row.get("PC cardinality")
    if pc_raw is None or pc_raw == "":
        vpc: Optional[int] = None
    else:
        try:
            vpc = int(pc_raw)
        except (TypeError, ValueError):
            vpc = None

    return {
        "vertical_note_count": vnc,
        "vertical_unique_pitch_count": vup,
        "vertical_pitch_class_cardinality": vpc,
    }


def _analysis_mode_label(xml_mode: MusicXmlImportMode | str | None) -> str:
    if xml_mode is None:
        return "unknown"
    if isinstance(xml_mode, str) and xml_mode.strip().lower() == "manual":
        return "manual"
    if isinstance(xml_mode, MusicXmlImportMode):
        mode = xml_mode
    else:
        try:
            mode = MusicXmlImportMode(str(xml_mode))
        except ValueError:
            if str(xml_mode).strip().lower() in ("manual", "aggregate"):
                return "manual"
            return "unknown"
    if mode == MusicXmlImportMode.ONSET_VERTICALITIES:
        return "onset_verticalities"
    if mode == MusicXmlImportMode.SOUNDING_VERTICALITIES:
        return "sounding_verticalities"
    if mode == MusicXmlImportMode.AGGREGATE:
        return "manual"
    return "unknown"


def _summary_statistics(series: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = [
        int(s["vertical_note_count"]) for s in series if s.get("vertical_note_count") is not None
    ]
    if not counts:
        return {
            "n_slices": len(series),
            "min_vertical_note_count": None,
            "max_vertical_note_count": None,
            "mean_vertical_note_count": None,
            "median_vertical_note_count": None,
            "std_vertical_note_count": None,
        }
    return {
        "n_slices": len(series),
        "min_vertical_note_count": min(counts),
        "max_vertical_note_count": max(counts),
        "mean_vertical_note_count": statistics.fmean(counts),
        "median_vertical_note_count": statistics.median(counts),
        "std_vertical_note_count": statistics.pstdev(counts) if len(counts) > 1 else 0.0,
    }


def build_vertical_cardinality_series(
    summary_rows: Sequence[Mapping[str, Any]],
    *,
    bin_cents: int,
    edo: int,
) -> List[Dict[str, Any]]:
    """One JSON series entry per slice-summary row (table order preserved)."""
    series: List[Dict[str, Any]] = []
    for slice_index, row in enumerate(summary_rows):
        card = vertical_cardinality_from_summary_row(row, bin_cents=bin_cents, edo=edo)
        try:
            time_q = parse_slice_time_quarters(row.get("Time (quarters)", row.get("Time")))
        except (TypeError, ValueError):
            time_q = float(slice_index)
        entry: Dict[str, Any] = {
            "slice_index": slice_index,
            "time_quarters": time_q,
        }
        entry.update(card)
        series.append(entry)
    return series


def build_vertical_cardinality_profile(
    *,
    input_file: str = "",
    analysis_mode: MusicXmlImportMode | str | None = None,
    deduplication_active: bool,
    edo: int,
    bin_cents: int,
    summary_rows: Optional[Sequence[Mapping[str, Any]]] = None,
    aggregate_notes: Optional[Sequence[NoteTuple]] = None,
) -> Dict[str, Any]:
    """
    Build ``vertical_cardinality_profile.json`` payload.

    Pass ``summary_rows`` for passage profiles, or ``aggregate_notes`` for a single
    aggregate sonority (``time_quarters`` = 0.0).
    """
    if summary_rows is not None and len(summary_rows) > 0:
        series = build_vertical_cardinality_series(summary_rows, bin_cents=bin_cents, edo=edo)
    elif aggregate_notes is not None:
        card = vertical_cardinality_for_notes(aggregate_notes, bin_cents=bin_cents, edo=edo)
        series = [{"slice_index": 0, "time_quarters": 0.0, **card}]
    else:
        series = []

    return {
        "schema_version": VERTICAL_CARDINALITY_SCHEMA_VERSION,
        "metric_family": "vertical_cardinality",
        "source": {
            "input_file": input_file,
            "analysis_mode": _analysis_mode_label(analysis_mode),
            "deduplication_active": bool(deduplication_active),
            "edo": int(edo),
        },
        "definitions": dict(DEFINITIONS),
        "time_unit": "quarters",
        "series": series,
        "summary_statistics": _summary_statistics(series),
    }


def vertical_cardinality_profile_json(
    profile: Mapping[str, Any],
    *,
    indent: int = 2,
) -> str:
    return json.dumps(profile, indent=indent, ensure_ascii=False)


def enrich_slice_summary_row(
    row: Dict[str, Any],
    slice_notes: Sequence[NoteTuple],
    *,
    bin_cents: int,
    edo: int,
) -> Dict[str, Any]:
    """
    Set ``Notes`` and optional transparency columns from the same prepared notes list.
    """
    card = vertical_cardinality_for_notes(slice_notes, bin_cents=bin_cents, edo=edo)
    row["Notes"] = card["vertical_note_count"]
    if card["vertical_unique_pitch_count"] is not None:
        row["Unique pitches"] = card["vertical_unique_pitch_count"]
    if card["vertical_pitch_class_cardinality"] is not None:
        row["PC cardinality"] = card["vertical_pitch_class_cardinality"]
    return row
