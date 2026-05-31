"""12-TET pitch-class set helpers (Forte / PC-set tradition), separate from pairwise metrics."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from iav.note_types import NoteTuple
from iav.pitch_model import chromatic_midi_float


def pitch_class_int_from_note(note: NoteTuple) -> Optional[int]:
    """Integer pitch class 0..11, or None if alter is not integral (microtone)."""
    letter, alter, octave = note
    if abs(alter - round(alter)) > 1e-6:
        return None
    s = int(round(chromatic_midi_float(letter, alter, octave)))
    return s % 12


def pitch_classes_12tet_unique(notes: Sequence[NoteTuple]) -> Optional[List[int]]:
    """
    Sorted unique pitch classes if every note maps to an integer chromatic step.
    Returns None if any note is microtonal off the 12-step grid.
    """
    pcs: List[int] = []
    for n in notes:
        pc = pitch_class_int_from_note(n)
        if pc is None:
            return None
        pcs.append(pc)
    return sorted(set(pcs))


def interval_vector_12tet(pcs: Sequence[int]) -> List[int]:
    """
    Allen Forte interval vector: counts of unordered pairs by interval class 1..6.
    Entries are [ic1, ic2, ic3, ic4, ic5, ic6].
    """
    pcs = sorted(set(int(p) % 12 for p in pcs))
    if len(pcs) < 2:
        return [0, 0, 0, 0, 0, 0]
    vec = [0, 0, 0, 0, 0, 0]
    for i in range(len(pcs)):
        for j in range(i + 1, len(pcs)):
            d = (pcs[j] - pcs[i]) % 12
            iclass = min(d, 12 - d)
            if 1 <= iclass <= 6:
                vec[iclass - 1] += 1
    return vec


def interval_vector_string(iv: Sequence[int]) -> str:
    return "<" + " ".join(str(x) for x in iv) + ">"


def prime_form_12tet(pcs: Sequence[int]) -> tuple[int, ...]:
    """
    Forte-style prime form: lexicographically smallest among all Tn and TnI,
    expressed as ascending pitch classes starting with 0.
    """
    pcs = sorted(set(int(p) % 12 for p in pcs))
    if not pcs:
        return ()
    if len(pcs) == 1:
        return (0,)
    candidates: list[tuple[int, ...]] = []
    for invert in (False, True):
        base = sorted({(-p) % 12 for p in pcs}) if invert else pcs[:]
        for t in range(12):
            transposed = sorted({(p + t) % 12 for p in base})
            m = transposed[0]
            norm = tuple(sorted((p - m) % 12 for p in transposed))
            candidates.append(norm)
    return min(candidates)


def normal_order_12tet(pcs: Sequence[int]) -> tuple[int, ...]:
    """
    Normal order: rotation of the sorted pitch-class cycle with smallest linear span
    (Straus / Rahn style), expressed from the lowest pitch of that window.
    """
    pcs = sorted(set(int(p) % 12 for p in pcs))
    if len(pcs) <= 1:
        return tuple(pcs)
    n = len(pcs)
    dups = pcs + [p + 12 for p in pcs]
    best: Optional[tuple[int, ...]] = None
    best_span: Optional[int] = None
    for start in range(n):
        window = dups[start : start + n]
        span = window[-1] - window[0]
        transposed = tuple(p - window[0] for p in window)
        if (
            best is None
            or best_span is None
            or span < best_span
            or (span == best_span and transposed < best)
        ):
            best_span = span
            best = transposed
    return best if best is not None else tuple(pcs)


def format_prime_form(pf: Sequence[int]) -> str:
    return "(" + " ".join(str(p) for p in pf) + ")"


def set_class_summary_12tet(notes: Sequence[NoteTuple]) -> Optional[Dict[str, Any]]:
    """
    If notes fit 12-TET pitch classes, return prime form, interval vector, and related labels.
    Otherwise return None.
    """
    pcs = pitch_classes_12tet_unique(notes)
    if pcs is None:
        return None
    pf = prime_form_12tet(pcs)
    iv = interval_vector_12tet(pcs)
    no = normal_order_12tet(pcs)
    return {
        "pitch_classes_sorted": pcs,
        "cardinality": len(pcs),
        "prime_form": pf,
        "prime_form_str": format_prime_form(pf),
        "interval_vector": iv,
        "interval_vector_str": interval_vector_string(iv),
        "normal_order": no,
        "normal_order_str": format_prime_form(no),
    }


__all__ = [
    "format_prime_form",
    "interval_vector_12tet",
    "interval_vector_string",
    "normal_order_12tet",
    "pitch_class_int_from_note",
    "pitch_classes_12tet_unique",
    "prime_form_12tet",
    "set_class_summary_12tet",
]
