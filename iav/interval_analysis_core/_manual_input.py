"""Manual table coercion, validation hints, deduplication, and alpha scheduling."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple, cast

from iav.note_types import NoteTuple
from iav.pitch_model import NOTE_BASE

from ._edo_labels import (
    _OCTAVE_SHORTHAND_IN_NOTE,
    format_note_display_label,
    note_to_units,
    parse_manual_note_string,
)


def _coerce_manual_table_rows(rows: Any) -> List[Dict[str, Any]]:
    """Normalize Streamlit data_editor output: None, empty list, or empty pandas.DataFrame → []."""
    if rows is None:
        return []
    try:
        import pandas as pd
    except ImportError:
        pd = None  # type: ignore[assignment]
    else:
        if isinstance(rows, pd.DataFrame):
            if rows.empty:
                return []
            return cast(List[Dict[str, Any]], rows.to_dict("records"))
    try:
        if len(rows) == 0:
            return []
    except TypeError:
        return []
    return list(rows)


def _default_octave_from_row(row: Dict[str, Any]) -> int:
    raw = row.get("Octave", row.get("Oitava", 4))
    if raw in ("", None):
        return 4
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 4


def normalize_manual_notes(rows):
    rows = _coerce_manual_table_rows(rows)
    notes: List[NoteTuple] = []
    errors: List[str] = []
    for idx, row in enumerate(rows, start=1):
        note_name = str(row.get("Note", "")).strip()
        if not note_name:
            continue
        parsed = parse_manual_note_string(note_name, default_octave=_default_octave_from_row(row))
        if parsed is None:
            errors.append(
                f"Row {idx}: could not read '{note_name}' (try C4, Eb5, F#3, or C with octave 4 by default)."
            )
            continue
        notes.append(parsed)
    return notes, errors


def looks_like_octave_shorthand_in_note_field(note_name: str) -> bool:
    """True if Note contains an explicit octave digit (e.g. C4, C 4), not pitch-class alone."""
    s = (note_name or "").strip()
    if not s:
        return False
    if _OCTAVE_SHORTHAND_IN_NOTE.match(s):
        return True
    letter = s[0:1].upper()
    if letter in NOTE_BASE and len(s) > 1:
        rest = s[1:].strip()
        if rest.isdigit():
            return True
    return False


def manual_input_hints(rows) -> List[str]:
    """
    Non-blocking hints for the manual table (duplicates, unusual octaves).

    Validation errors still come from ``normalize_manual_notes``; hints do not replace those.
    """
    rows = _coerce_manual_table_rows(rows)
    hints: List[str] = []
    parsed_by_index: List[Tuple[int, NoteTuple]] = []

    for idx, row in enumerate(rows, start=1):
        note_name = str(row.get("Note", "")).strip()
        if not note_name:
            continue
        parsed = parse_manual_note_string(note_name, default_octave=_default_octave_from_row(row))
        if parsed is None:
            continue
        parsed_by_index.append((idx, parsed))

    first_row_for_pitch: Dict[NoteTuple, int] = {}
    for idx, nt in parsed_by_index:
        if nt in first_row_for_pitch:
            hints.append(
                f"Row {idx}: duplicate pitch of row {first_row_for_pitch[nt]} "
                f"({format_note_display_label(*nt)}); dedupe may collapse these."
            )
        else:
            first_row_for_pitch[nt] = idx
        _l, _a, o = nt
        if o < 1 or o > 8:
            hints.append(
                f"Row {idx}: octave {o} is outside the usual concert range (about 1–8); verify intent."
            )

    return hints


def dedupe_notes_by_midi(notes: Sequence[NoteTuple], bin_cents: int = 100):
    seen = set()
    out: List[NoteTuple] = []
    for n in notes:
        u = note_to_units(*n, bin_cents=bin_cents)
        if u in seen:
            continue
        seen.add(u)
        out.append(n)
    return out


def compute_alpha_used(note_count: int, alpha_base: float, auto_alpha: bool, k_auto: int):
    n_adj = max(1, note_count - 1)
    if auto_alpha and note_count >= 3 and n_adj >= 2:
        return alpha_base + (1.0 - alpha_base) * ((n_adj - 1) / ((n_adj - 1) + float(k_auto)))
    return alpha_base
