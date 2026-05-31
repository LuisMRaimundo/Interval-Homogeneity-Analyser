"""Combine manual and MusicXML pitch lists (no Streamlit dependency)."""

from __future__ import annotations

from typing import List

from iav.note_types import NoteTuple


def assemble_notes_from_manual_and_xml(
    manual_notes: List[NoteTuple],
    xml_notes: List[NoteTuple],
    has_xml_upload: bool,
    merge_manual: bool,
) -> List[NoteTuple]:
    """
    Build the final pitch list from manual entry and/or MusicXML.

    Without an XML upload, only manual notes are used. With XML, manual notes are included only
    when ``merge_manual`` is True and the manual table produced at least one valid pitch.
    """
    if not has_xml_upload:
        return list(manual_notes)
    if merge_manual and manual_notes:
        return manual_notes + xml_notes
    return list(xml_notes)
