"""Shared note tuple type used across analytics and MusicXML ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

# (letter, alter semitones relative to natural, octave as in scientific pitch notation)
NoteTuple = Tuple[str, float, int]


@dataclass(frozen=True, slots=True)
class SpelledPitch:
    """Scientific pitch spelling (letter + chromatic alter + octave)."""

    letter: str
    alter: float
    octave: int

    @classmethod
    def from_tuple(cls, note: NoteTuple) -> SpelledPitch:
        letter, alter, octave = note
        return cls(letter=str(letter), alter=float(alter), octave=int(octave))

    def as_tuple(self) -> NoteTuple:
        return (self.letter, self.alter, self.octave)


__all__ = ["NoteTuple", "SpelledPitch"]
