"""Focused tests for ``iav.musicxml_io._flat_score`` flat MusicXML extraction."""

from __future__ import annotations

import io
import zipfile

import pytest
from defusedxml import ElementTree as ET

from iav.musicxml_io._flat_score import (
    _parse_musicxml_bytes_flat,
    get_musicxml_bytes,
    parse_musicxml_bytes,
    parse_musicxml_bytes_with_sounding_transpose,
)

_SCORE_OPEN = '<?xml version="1.0" encoding="UTF-8"?>\n<score-partwise version="3.1">\n'
_SCORE_CLOSE = "</score-partwise>"


def _score_xml(body: str) -> bytes:
    return f"{_SCORE_OPEN}{body}{_SCORE_CLOSE}".encode("utf-8")


def _wrap_part(measures: str, part_id: str = "P1") -> bytes:
    return _score_xml(f'<part id="{part_id}">{measures}</part>')


def _measure(inner: str, number: str = "1", attributes: str = "") -> str:
    attrs = f"<attributes>{attributes}</attributes>" if attributes else ""
    return f'<measure number="{number}">{attrs}{inner}</measure>'


def _note(step: str, octave: int, *, alter: str | None = None, accidental: str | None = None) -> str:
    alter_xml = f"<alter>{alter}</alter>" if alter is not None else ""
    acc_xml = f"<accidental>{accidental}</accidental>" if accidental else ""
    return (
        f"<note><pitch><step>{step}</step>{alter_xml}<octave>{octave}</octave></pitch>"
        f"<duration>1</duration>{acc_xml}</note>"
    )


def _chord_note(step: str, octave: int, *, alter: str | None = None) -> str:
    alter_xml = f"<alter>{alter}</alter>" if alter is not None else ""
    return (
        f"<note><chord/><pitch><step>{step}</step>{alter_xml}<octave>{octave}</octave></pitch>"
        f"<duration>1</duration></note>"
    )


def _rest() -> str:
    return "<note><rest/><duration>1</duration></note>"


def _make_mxl(
    score_xml: bytes,
    *,
    include_container: bool = True,
    score_name: str = "score.xml",
    extra_entries: list[tuple[str, bytes]] | None = None,
) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(score_name, score_xml)
        if include_container:
            container = (
                '<?xml version="1.0"?>'
                "<container><rootfiles>"
                f'<rootfile full-path="{score_name}"/>'
                "</rootfiles></container>"
            )
            zf.writestr("META-INF/container.xml", container)
        if extra_entries:
            for name, data in extra_entries:
                zf.writestr(name, data)
    return buf.getvalue()


# --- Audit note (public API via dispatch) ---
# Public: get_musicxml_bytes, parse_musicxml_bytes, parse_musicxml_bytes_with_sounding_transpose
# Internal: _parse_musicxml_bytes_flat (transpose flag + traversal)


def test_parse_empty_score_returns_empty_list():
    notes, skipped = parse_musicxml_bytes(_score_xml(""))
    assert notes == []
    assert skipped == 0


def test_parse_part_with_rest_only_returns_empty_list():
    xml = _wrap_part(_measure(_rest()))
    notes, skipped = parse_musicxml_bytes(xml)
    assert notes == []
    assert skipped == 0


def test_parse_single_note_tuple_shape():
    xml = _wrap_part(_measure(_note("C", 4)))
    notes, skipped = parse_musicxml_bytes(xml)
    assert skipped == 0
    assert notes == [("C", 0.0, 4)]


def test_parse_sequential_notes_preserve_order():
    inner = _note("C", 4) + _note("D", 4) + _note("E", 4)
    notes, skipped = parse_musicxml_bytes(_wrap_part(_measure(inner)))
    assert skipped == 0
    assert notes == [("C", 0.0, 4), ("D", 0.0, 4), ("E", 0.0, 4)]


def test_parse_chord_includes_all_simultaneous_tones():
    inner = _note("C", 4) + _chord_note("E", 4) + _chord_note("G", 4)
    notes, skipped = parse_musicxml_bytes(_wrap_part(_measure(inner)))
    assert skipped == 0
    assert notes == [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]


def test_parse_rest_between_pitched_notes():
    inner = _note("C", 4) + _rest() + _note("G", 4)
    notes, skipped = parse_musicxml_bytes(_wrap_part(_measure(inner)))
    assert notes == [("C", 0.0, 4), ("G", 0.0, 4)]
    assert skipped == 0


@pytest.mark.parametrize(
    ("alter", "accidental", "expected_alter"),
    [
        (None, None, 0.0),
        ("1", None, 1.0),
        ("-1", None, -1.0),
        ("0", None, 0.0),
        (None, "sharp", 1.0),
        (None, "flat", -1.0),
        (None, "natural", 0.0),
    ],
)
def test_parse_accidentals_and_alter(alter, accidental, expected_alter):
    inner = _measure(_note("F", 4, alter=alter, accidental=accidental))
    notes, skipped = parse_musicxml_bytes(_wrap_part(inner))
    assert skipped == 0
    assert len(notes) == 1
    assert notes[0][0] == "F"
    assert notes[0][1] == pytest.approx(expected_alter)
    assert notes[0][2] == 4


@pytest.mark.parametrize(
    "pitch_xml",
    [
        "<note><duration>1</duration></note>",
        "<note><pitch><octave>4</octave></pitch><duration>1</duration></note>",
        "<note><pitch><step>C</step></pitch><duration>1</duration></note>",
        "<note><pitch><step>C</step><octave>not-int</octave></pitch><duration>1</duration></note>",
        "<note><pitch><step>X</step><octave>4</octave></pitch><duration>1</duration></note>",
    ],
)
def test_parse_malformed_pitch_is_skipped(pitch_xml: str):
    notes, skipped = parse_musicxml_bytes(_wrap_part(_measure(pitch_xml)))
    assert notes == []
    assert skipped == 0


def test_parse_invalid_alter_text_increments_skipped():
    inner = _measure(
        '<note><pitch><step>C</step><alter>bad</alter><octave>4</octave></pitch><duration>1</duration></note>'
    )
    notes, skipped = parse_musicxml_bytes(_wrap_part(inner))
    assert notes == []
    assert skipped == 1


def test_parse_multiple_measures_and_parts_preserve_traversal_order():
    part1 = _measure(_note("C", 4), number="1") + _measure(_note("D", 4), number="2")
    part2 = _measure(_note("E", 5), number="1")
    xml = _score_xml(f'<part id="P1">{part1}</part><part id="P2">{part2}</part>')
    notes, skipped = parse_musicxml_bytes(xml)
    assert skipped == 0
    assert notes == [("C", 0.0, 4), ("D", 0.0, 4), ("E", 0.0, 5)]


def test_parse_measure_without_divisions_or_duration_still_extracts_pitch():
    inner = _measure('<note><pitch><step>A</step><octave>3</octave></pitch></note>')
    notes, skipped = parse_musicxml_bytes(_wrap_part(inner))
    assert notes == [("A", 0.0, 3)]
    assert skipped == 0


def test_get_musicxml_bytes_non_zip_returns_same_bytes():
    xml = _wrap_part(_measure(_note("B", 3)))
    assert get_musicxml_bytes(xml) == xml


def test_get_musicxml_bytes_plain_xml_passthrough():
    """Alias for non-ZIP passthrough (target 1)."""
    xml = _wrap_part(_measure(_note("B", 3)))
    assert get_musicxml_bytes(xml) == xml


def test_get_musicxml_bytes_mxl_valid_container_returns_score_xml_bytes():
    xml = _wrap_part(_measure(_note("C", 4)))
    mxl = _make_mxl(xml, score_name="score.xml")
    assert get_musicxml_bytes(mxl) == xml


def test_get_musicxml_bytes_mxl_missing_container_rootfile_falls_back_to_xml():
    xml = _wrap_part(_measure(_note("F", 4)))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("fallback.xml", xml)
        container = (
            '<?xml version="1.0"?>'
            "<container><rootfiles>"
            '<rootfile full-path="missing-score.xml"/>'
            "</rootfiles></container>"
        )
        zf.writestr("META-INF/container.xml", container)
    assert get_musicxml_bytes(buf.getvalue()) == xml


def test_get_musicxml_bytes_mxl_falls_back_to_musicxml_extension():
    xml = _wrap_part(_measure(_note("G", 4)))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("piece.musicxml", xml)
    assert get_musicxml_bytes(buf.getvalue()) == xml


def test_get_musicxml_bytes_mxl_with_container():
    xml = _wrap_part(_measure(_note("C", 4)))
    mxl = _make_mxl(xml)
    extracted = get_musicxml_bytes(mxl)
    assert extracted is not None
    notes, skipped = parse_musicxml_bytes(mxl)
    assert notes == [("C", 0.0, 4)]
    assert skipped == 0


def test_get_musicxml_bytes_mxl_without_container_falls_back_to_first_xml():
    xml = _wrap_part(_measure(_note("D", 4)))
    mxl = _make_mxl(xml, include_container=False)
    extracted = get_musicxml_bytes(mxl)
    assert extracted == xml
    notes, _ = parse_musicxml_bytes(mxl)
    assert notes == [("D", 0.0, 4)]


def test_get_musicxml_bytes_mxl_invalid_container_falls_back_to_first_xml():
    xml = _wrap_part(_measure(_note("E", 4)))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("score.xml", xml)
        zf.writestr("META-INF/container.xml", b"<<broken")
    mxl_broken = buf.getvalue()
    assert get_musicxml_bytes(mxl_broken) == xml


def test_get_musicxml_bytes_mxl_without_xml_returns_none():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", b"no music here")
    assert get_musicxml_bytes(buf.getvalue()) is None
    notes, skipped = parse_musicxml_bytes(buf.getvalue())
    assert notes == []
    assert skipped == 0


def test_get_musicxml_bytes_rejects_too_many_zip_entries(monkeypatch):
    monkeypatch.setattr(
        "iav.musicxml_io._flat_score.MAX_ZIP_FILES",
        2,
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("a.txt", b"a")
        zf.writestr("b.txt", b"b")
        zf.writestr("c.txt", b"c")
    with pytest.raises(ValueError, match="too many files"):
        get_musicxml_bytes(buf.getvalue())


def test_parse_musicxml_bytes_flat_returns_empty_when_get_musicxml_bytes_none(monkeypatch):
    monkeypatch.setattr("iav.musicxml_io._flat_score.get_musicxml_bytes", lambda _b: None)
    notes, skipped = _parse_musicxml_bytes_flat(b"zip-or-xml", apply_musicxml_transpose=False)
    assert notes == []
    assert skipped == 0


def test_parse_musicxml_bytes_minimal_valid_score_one_note():
    xml = _wrap_part(_measure(_note("A", 3)))
    notes, skipped = parse_musicxml_bytes(xml)
    assert len(notes) >= 1
    assert notes[0] == ("A", 0.0, 3)
    assert skipped == 0


def test_get_musicxml_bytes_rejects_oversized_uncompressed_payload(monkeypatch):
    monkeypatch.setattr(
        "iav.musicxml_io._flat_score.MAX_ZIP_UNCOMPRESSED_BYTES",
        8,
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("big.xml", b"x" * 32)
    with pytest.raises(ValueError, match="too large"):
        get_musicxml_bytes(buf.getvalue())


def test_parse_with_sounding_transpose_applies_measure_transpose():
    body = (
        _measure(
            _note("D", 4),
            attributes="<divisions>1</divisions><transpose><chromatic>-2</chromatic></transpose>",
        )
    )
    xml = _wrap_part(body)
    written, _ = parse_musicxml_bytes(xml)
    sounding, _ = parse_musicxml_bytes_with_sounding_transpose(xml)
    assert written == [("D", 0.0, 4)]
    assert sounding == [("C", 0.0, 4)]


def test_parse_invalid_xml_raises_parse_error():
    with pytest.raises(ET.ParseError):
        parse_musicxml_bytes(b"<not-well-formed")
