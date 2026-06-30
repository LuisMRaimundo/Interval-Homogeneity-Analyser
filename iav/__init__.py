"""Interval_Homogeneity — primary Python package (analytics + Streamlit helpers)."""

from .analysis_enums import HomogeneityMethod
from .constants import FORCE_DEDUPE_THRESHOLD, MAX_NOTES
from .note_types import NoteTuple, SpelledPitch

__all__ = ["MAX_NOTES", "FORCE_DEDUPE_THRESHOLD", "NoteTuple", "SpelledPitch", "HomogeneityMethod"]
