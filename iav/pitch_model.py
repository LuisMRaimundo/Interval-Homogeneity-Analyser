"""
Canonical 12-TET pitch height and MusicXML accidental tokens.

Interval analysis uses **floating-point chromatic MIDI** (semitones; same convention as
``(octave + 1) * 12 + diatonic_pc + alter``). Letter / alter / octave tuples are
**spellings** for I/O and display; distances and homogeneity are always derived from
``chromatic_midi_float`` (or quantized cents via ``iav.interval_analysis_core.note_to_units``).

**Transposition / orthography:** when MusicXML ``<transpose>`` is applied, the parser
normalizes to a **sharp-leaning chromatic spelling** via ``spelled_note_from_chromatic_midi``.
That preserves **sounding height** for intervals and generic display, but **not** original
engraver spelling (e.g. flat vs sharp for the same pitch class). For spelling-sensitive work,
use concert-pitch import (ignore transpose) or a dedicated spelling-preserving path—not this
canonical respelling alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

NOTE_BASE = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}

# MusicXML <accidental> text (lowercased) → semitone offset
ACCIDENTAL_TOKENS = {
    "natural": 0.0,
    "sharp": 1.0,
    "flat": -1.0,
    "double-sharp": 2.0,
    "double-flat": -2.0,
    "half-sharp": 0.5,
    "half-flat": -0.5,
    "quarter-sharp": 0.5,
    "quarter-flat": -0.5,
    "three-quarters-sharp": 1.5,
    "three-quarters-flat": -1.5,
}

MICROTONAL_ACCIDENTALS = frozenset(
    {
        "quarter-sharp",
        "quarter-flat",
        "half-sharp",
        "half-flat",
        "three-quarters-sharp",
        "three-quarters-flat",
    }
)

# After transpose: map chromatic pitch-class floor to sharp-leaning spelling (integer steps 0..11).
_PC_TO_SHARP_SPELLING = (
    (0, "C", 0.0),
    (1, "C", 1.0),
    (2, "D", 0.0),
    (3, "D", 1.0),
    (4, "E", 0.0),
    (5, "F", 0.0),
    (6, "F", 1.0),
    (7, "G", 0.0),
    (8, "G", 1.0),
    (9, "A", 0.0),
    (10, "A", 1.0),
    (11, "B", 0.0),
)

NoteSpelling = Tuple[str, float, int]


def chromatic_midi_float(letter: str, alter: float, octave: int) -> float:
    """Absolute 12-TET pitch in semitones (middle C = MIDI 60 at C4)."""
    return (octave + 1) * 12.0 + float(NOTE_BASE[letter]) + float(alter)


def spelled_note_from_chromatic_midi(total_midi: float) -> NoteSpelling:
    """
    Map sounding MIDI (float; may include microtones) to a normalized ``(letter, alter, octave)``.

    ``alter`` is the residual from ``NOTE_BASE[letter]`` so that the tuple reproduces ``total_midi``
    under ``chromatic_midi_float``.
    """
    octave_out = int(math.floor(total_midi / 12.0)) - 1
    rem = total_midi - (octave_out + 1) * 12.0
    while rem < 0.0:
        rem += 12.0
        octave_out -= 1
    while rem >= 12.0:
        rem -= 12.0
        octave_out += 1

    k_floor = int(math.floor(rem + 1e-12))
    k = k_floor % 12
    _pc_int, letter, _base_alter = _PC_TO_SHARP_SPELLING[k]
    alter_out = rem - float(NOTE_BASE[letter])
    return letter, alter_out, octave_out


@dataclass(frozen=True, slots=True)
class AnalyzedPitch:
    """Sonic height in semitones; optional score spelling from the user or MusicXML."""

    midi_semitones: float
    spelling: Optional[NoteSpelling] = None

    @classmethod
    def from_spelling(cls, letter: str, alter: float, octave: int) -> AnalyzedPitch:
        m = chromatic_midi_float(letter, alter, octave)
        return cls(midi_semitones=m, spelling=(letter, float(alter), int(octave)))


def midis_from_spellings(notes: Iterable[NoteSpelling]) -> list[float]:
    """Project spellings to MIDI floats (single definition path for interval size)."""
    return [chromatic_midi_float(letter, alter, octave) for letter, alter, octave in notes]


__all__ = [
    "ACCIDENTAL_TOKENS",
    "MICROTONAL_ACCIDENTALS",
    "NOTE_BASE",
    "AnalyzedPitch",
    "NoteSpelling",
    "chromatic_midi_float",
    "midis_from_spellings",
    "spelled_note_from_chromatic_midi",
]
