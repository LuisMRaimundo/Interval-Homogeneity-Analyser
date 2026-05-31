"""Secure MusicXML / MXL ingestion and pitch extraction (no Streamlit)."""

from __future__ import annotations

from ._flat_score import (
    MAX_ZIP_FILES,
    MAX_ZIP_UNCOMPRESSED_BYTES,
    get_musicxml_bytes,
    parse_musicxml_bytes,
    parse_musicxml_bytes_with_sounding_transpose,
)
from ._onset_verticalities import (
    parse_musicxml_verticalities_bytes,
    parse_musicxml_verticalities_bytes_with_sounding_transpose,
)
from ._dispatch import parse_musicxml_upload
from ._sounding_verticalities import (
    parse_musicxml_sounding_verticalities_bytes,
    parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose,
)
from ._xml_primitives import (
    extract_pitch_from_note,
    find_child_by_suffix,
    tie_types_from_note,
    transpose_from_attributes,
)

__all__ = [
    "MAX_ZIP_FILES",
    "MAX_ZIP_UNCOMPRESSED_BYTES",
    "extract_pitch_from_note",
    "find_child_by_suffix",
    "get_musicxml_bytes",
    "parse_musicxml_bytes",
    "parse_musicxml_bytes_with_sounding_transpose",
    "parse_musicxml_upload",
    "parse_musicxml_sounding_verticalities_bytes",
    "parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose",
    "parse_musicxml_verticalities_bytes",
    "parse_musicxml_verticalities_bytes_with_sounding_transpose",
    "tie_types_from_note",
    "transpose_from_attributes",
]
