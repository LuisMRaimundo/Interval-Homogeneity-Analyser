"""
Backward-compatible shim: MusicXML parsing lives in ``iav.musicxml_io``.

Prefer ``from iav.musicxml_io import ...`` in new code.
"""

from __future__ import annotations

from iav.musicxml_io import *  # noqa: F403

__all__ = [
    "MAX_ZIP_FILES",
    "MAX_ZIP_UNCOMPRESSED_BYTES",
    "extract_pitch_from_note",
    "find_child_by_suffix",
    "get_musicxml_bytes",
    "parse_musicxml_bytes",
    "parse_musicxml_bytes_with_sounding_transpose",
    "parse_musicxml_sounding_verticalities_bytes",
    "parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose",
    "parse_musicxml_verticalities_bytes",
    "parse_musicxml_verticalities_bytes_with_sounding_transpose",
    "tie_types_from_note",
    "transpose_from_attributes",
]
