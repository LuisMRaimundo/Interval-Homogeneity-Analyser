"""MXL container handling and flat (non-temporal) pitch list extraction."""

from __future__ import annotations

import io
import zipfile

from defusedxml import ElementTree as ET

from ._xml_primitives import (
    extract_pitch_from_note,
    find_child_by_suffix,
    transpose_from_attributes,
)

MAX_ZIP_FILES = 2000
MAX_ZIP_UNCOMPRESSED_BYTES = 20 * 1024 * 1024


def get_musicxml_bytes(file_bytes):
    if not zipfile.is_zipfile(io.BytesIO(file_bytes)):
        return file_bytes
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_FILES:
            raise ValueError("Compressed MusicXML contains too many files.")
        total_uncompressed = sum(info.file_size for info in infos)
        if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
            raise ValueError("Compressed MusicXML is too large when decompressed.")
        xml_bytes = None
        try:
            container_bytes = zf.read("META-INF/container.xml")
            container_root = ET.fromstring(container_bytes)
            for rootfile in container_root.iter():
                if rootfile.tag.endswith("rootfile"):
                    full_path = rootfile.attrib.get("full-path")
                    if full_path and full_path in zf.namelist():
                        xml_bytes = zf.read(full_path)
                        break
        except KeyError:
            xml_bytes = None
        except ET.ParseError:
            xml_bytes = None

        if xml_bytes is None:
            xml_names = [n for n in zf.namelist() if n.endswith(".xml") or n.endswith(".musicxml")]
            if not xml_names:
                return None
            xml_bytes = zf.read(xml_names[0])
        return xml_bytes


def _parse_musicxml_bytes_flat(file_bytes, *, apply_musicxml_transpose: bool):
    xml_bytes = get_musicxml_bytes(file_bytes)
    if xml_bytes is None:
        return [], 0
    root = ET.fromstring(xml_bytes)
    notes = []
    skipped_microtonal = 0
    for part in root.iter():
        if not part.tag.endswith("part"):
            continue
        current_transpose = 0.0
        for measure in part:
            if not measure.tag.endswith("measure"):
                continue
            attributes = find_child_by_suffix(measure, "attributes")
            if attributes is not None and apply_musicxml_transpose:
                current_transpose = transpose_from_attributes(attributes)
            for note in measure:
                if not note.tag.endswith("note"):
                    continue
                note_tuple, skipped = extract_pitch_from_note(note, current_transpose)
                skipped_microtonal += skipped
                if note_tuple is not None:
                    notes.append(note_tuple)
    return notes, skipped_microtonal


def parse_musicxml_bytes(file_bytes):
    """
    Flatten pitched notes from MusicXML using **written** ``<pitch>`` data only.

    MusicXML ``<transpose>`` is **not** applied (same behaviour as the Streamlit app).
    """
    return _parse_musicxml_bytes_flat(file_bytes, apply_musicxml_transpose=False)


def parse_musicxml_bytes_with_sounding_transpose(file_bytes):
    """
    Same as ``parse_musicxml_bytes``, but applies each measure's ``<transpose>`` to sounding height
    and rewrites spellings via ``spelled_note_from_chromatic_midi``. For **regression tests** and
    advanced scripting—not used by the GUI.
    """
    return _parse_musicxml_bytes_flat(file_bytes, apply_musicxml_transpose=True)
