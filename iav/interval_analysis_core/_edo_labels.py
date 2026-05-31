"""EDO grid labels, manual spelling helpers, and pairwise interval naming."""

from __future__ import annotations

import itertools
import math
import re
from typing import Dict, Optional, Sequence, Tuple

from iav.note_types import NoteTuple
from iav.pitch_model import NOTE_BASE, chromatic_midi_float

_OCTAVE_SHORTHAND_IN_NOTE = re.compile(r"^[A-Ga-g]\d+$", re.IGNORECASE)
_OCTAVE_SUFFIX_IN_MANUAL = re.compile(r"^(?P<pitch>.+?)\s*(?P<oct>\d{1,2})$")

ACC_TO_SEMITONES = {
    "": 0.0,
    "#": 1.0,
    "##": 2.0,
    "x": 2.0,
    "b": -1.0,
    "bb": -2.0,
    "♯": 1.0,
    "𝄪": 2.0,
    "♭": -1.0,
    "𝄫": -2.0,
    "+": 0.5,
    "-": -0.5,
    "↑": 0.5,
    "↓": -0.5,
}

ENHARMONIC_SIMPLE = {
    0: ("P", 1),
    1: ("m", 2),
    2: ("M", 2),
    3: ("m", 3),
    4: ("M", 3),
    5: ("P", 4),
    6: ("TT", 4),
    7: ("P", 5),
    8: ("m", 6),
    9: ("M", 6),
    10: ("m", 7),
    11: ("M", 7),
}


def parse_note_name(note_name: str):
    """Parse manual note names like C, D#, Eb, F##, Bb, C+ (quarter-sharp)."""
    note_name = note_name.strip()
    if not note_name:
        return None
    if _OCTAVE_SHORTHAND_IN_NOTE.match(note_name):
        return None
    letter = note_name[0].upper()
    if letter not in NOTE_BASE:
        return None
    accidental = note_name[1:].strip()
    if accidental.isdigit():
        return None
    if accidental in ACC_TO_SEMITONES:
        return letter, ACC_TO_SEMITONES[accidental]
    try:
        alter = float(accidental)
    except ValueError:
        return None
    return letter, alter


def parse_manual_note_string(
    note_name: str,
    default_octave: int = 4,
) -> Optional[Tuple[str, float, int]]:
    """
    Parse manual / MusicXML editor strings: C4, Eb5, C#, Bb3, C+4, or C with a default octave.
    """
    s = (note_name or "").strip().replace("\t", " ")
    if not s:
        return None
    letter = s[0].upper()
    if letter not in NOTE_BASE:
        return None
    tail = s[1:].strip()
    try:
        fallback_oct = int(default_octave)
    except (TypeError, ValueError):
        fallback_oct = 4

    trials: list[Tuple[str, int]] = []
    if not tail:
        trials.append(("", fallback_oct))
    elif tail.isdigit():
        trials.append(("", int(tail)))
    else:
        m = _OCTAVE_SUFFIX_IN_MANUAL.match(tail)
        if m:
            trials.append((m.group("pitch").strip(), int(m.group("oct"))))
        trials.append((tail, fallback_oct))

    for body, octave in trials:
        label = letter + body if body else letter
        parsed = parse_note_name(label)
        if parsed is not None:
            ltr, alter = parsed
            return ltr, float(alter), octave
    return None


def format_note_spelling(letter: str, alter: float) -> str:
    """
    Pitch-class spelling without octave: C, C#, Bb, C+, etc.
    Same accidental rules as manual entry (parse_note_name / ACC_TO_SEMITONES).
    """
    a = float(alter)
    matches = [(s, v) for s, v in ACC_TO_SEMITONES.items() if abs(v - a) < 1e-6]
    if matches:
        preference = (
            "##",
            "#",
            "bb",
            "b",
            "x",
            "+",
            "-",
            "↑",
            "↓",
            "♯",
            "♭",
            "𝄪",
            "𝄫",
            "",
        )
        for pref in preference:
            for s, v in matches:
                if s == pref:
                    return f"{letter}{s}"
        s, _ = matches[0]
        return f"{letter}{s}"
    return f"{letter}({a:+.2f}st)"


def format_note_display_label(letter: str, alter: float, octave: int) -> str:
    """
    Spelling for charts and tables: C4, C#4, Bb4, C+4 (quarter-tone), etc.
    Uses the same accidental tokens as manual entry where possible.
    """
    return f"{format_note_spelling(letter, alter)}{octave}"


def quantize_units(value: float) -> int:
    if value >= 0:
        return int(math.floor(value + 0.5))
    return -int(math.floor(-value + 0.5))


def note_to_units(letter: str, alter: float, octave: int, bin_cents: int = 100) -> int:
    cents = chromatic_midi_float(letter, alter, octave) * 100.0
    return quantize_units(cents / float(bin_cents))


def semitone_to_label(semitones: int) -> str:
    if semitones < 0:
        raise ValueError("semitones must be non-negative")
    octaves = semitones // 12
    simple = semitones % 12
    quality, simple_number = ENHARMONIC_SIMPLE[simple]
    number = simple_number + 7 * octaves
    return f"TT{number}" if quality == "TT" else f"{quality}{number}"


def units_to_label(units: int, bin_cents: int = 100) -> str:
    if units < 0:
        raise ValueError("units must be non-negative")
    if bin_cents == 100:
        return semitone_to_label(units)
    return f"{units * bin_cents:.0f}c"


def interval_name(lower: NoteTuple, upper: NoteTuple, bin_cents: int = 100):
    lower_letter, lower_alter, lower_octave = lower
    upper_letter, upper_alter, upper_octave = upper
    lower_units = note_to_units(lower_letter, lower_alter, lower_octave, bin_cents)
    upper_units = note_to_units(upper_letter, upper_alter, upper_octave, bin_cents)
    if upper_units < lower_units:
        lower_units, upper_units = upper_units, lower_units
    unit_diff = upper_units - lower_units
    return units_to_label(unit_diff, bin_cents), unit_diff


def intervals_for_notes(notes: Sequence[NoteTuple], bin_cents: int = 100):
    interval_counts: Dict[str, int] = {}
    distance_counts: Dict[int, int] = {}
    for lower, upper in itertools.combinations(notes, 2):
        name, unit_diff = interval_name(lower, upper, bin_cents)
        interval_counts[name] = interval_counts.get(name, 0) + 1
        distance_counts[unit_diff] = distance_counts.get(unit_diff, 0) + 1
    return interval_counts, distance_counts
