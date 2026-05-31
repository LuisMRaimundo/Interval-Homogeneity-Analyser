"""Route MusicXML bytes to the correct parser (written vs sounding transpose)."""

from __future__ import annotations

from typing import Any, List, Tuple, Union

from iav.analysis_enums import MusicXmlImportMode
from iav.note_types import NoteTuple

from ._flat_score import parse_musicxml_bytes, parse_musicxml_bytes_with_sounding_transpose
from ._onset_verticalities import (
    parse_musicxml_verticalities_bytes,
    parse_musicxml_verticalities_bytes_with_sounding_transpose,
)
from ._sounding_verticalities import (
    parse_musicxml_sounding_verticalities_bytes,
    parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose,
)

SliceList = List[dict[str, Any]]
ParseResult = Union[Tuple[List[NoteTuple], int], Tuple[SliceList, int]]


def parse_musicxml_upload(
    file_bytes: bytes,
    mode: MusicXmlImportMode,
    *,
    include_grace: bool,
    include_cue: bool,
    apply_sounding_transpose: bool,
) -> ParseResult:
    """
    Parse uploaded MusicXML for the given import mode.

    When ``apply_sounding_transpose`` is True, each measure's ``<transpose>`` is applied
    (concert-pitch height for transposing instruments).
    """
    if mode == MusicXmlImportMode.AGGREGATE:
        if apply_sounding_transpose:
            return parse_musicxml_bytes_with_sounding_transpose(file_bytes)
        return parse_musicxml_bytes(file_bytes)
    if mode == MusicXmlImportMode.SOUNDING_VERTICALITIES:
        if apply_sounding_transpose:
            return parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose(file_bytes)
        return parse_musicxml_sounding_verticalities_bytes(file_bytes)
    if apply_sounding_transpose:
        return parse_musicxml_verticalities_bytes_with_sounding_transpose(
            file_bytes, include_grace=include_grace, include_cue=include_cue
        )
    return parse_musicxml_verticalities_bytes(
        file_bytes, include_grace=include_grace, include_cue=include_cue
    )
