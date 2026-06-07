"""Focused tests for ``iav.musicxml_io._measure_voice_cursor`` timeline helpers."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from iav.musicxml_io._measure_voice_cursor import (
    VoiceTimelineState,
    begin_measure,
    handle_backup_or_forward,
    quarter_duration_for_note,
    voice_and_staff_keys,
)

# ``begin_measure`` applies the first <attributes> block (no separate
# ``update_state_from_attributes`` helper in this module).


def _sub(tag: str, text: str | None = None) -> ET.Element:
    elem = ET.Element(tag)
    if text is not None:
        elem.text = text
    return elem


def _measure(*children: ET.Element) -> ET.Element:
    measure = ET.Element("measure")
    for child in children:
        measure.append(child)
    return measure


def _fresh_state(**kwargs) -> VoiceTimelineState:
    state = VoiceTimelineState()
    for key, value in kwargs.items():
        setattr(state, key, value)
    state.voice_time["1"] = 3.0
    state.last_onset["1"] = 2.0
    state.cursor_time = 1.5
    return state


def test_begin_measure_attributes_none_preserves_divisions_and_transpose():
    state = _fresh_state(current_divisions=6, current_transpose=-2.0, measure_offset=4.0)
    begin_measure(_measure(), state, apply_musicxml_transpose=False)
    assert state.current_divisions == 6
    assert state.current_transpose == -2.0
    assert state.measure_offset == 4.0
    assert state.voice_time == {}
    assert state.last_onset == {}
    assert state.cursor_time == 0.0


def test_begin_measure_missing_divisions_keeps_current_divisions():
    attrs = ET.Element("attributes")
    attrs.append(_sub("clef"))
    state = VoiceTimelineState(current_divisions=8)
    begin_measure(_measure(attrs), state, apply_musicxml_transpose=False)
    assert state.current_divisions == 8


def test_begin_measure_valid_divisions_updates_state():
    attrs = ET.Element("attributes")
    attrs.append(_sub("divisions", "4"))
    state = VoiceTimelineState(current_divisions=1)
    begin_measure(_measure(attrs), state, apply_musicxml_transpose=False)
    assert state.current_divisions == 4


def test_begin_measure_invalid_divisions_falls_back_to_previous_or_one():
    attrs = ET.Element("attributes")
    attrs.append(_sub("divisions", "bad"))
    state = VoiceTimelineState(current_divisions=8)
    begin_measure(_measure(attrs), state, apply_musicxml_transpose=False)
    assert state.current_divisions == 8

    state_zero = VoiceTimelineState(current_divisions=0)
    begin_measure(_measure(attrs), state_zero, apply_musicxml_transpose=False)
    assert state_zero.current_divisions == 1


def test_begin_measure_transpose_applied_only_when_requested():
    attrs = ET.Element("attributes")
    attrs.append(_sub("divisions", "1"))
    transpose = ET.Element("transpose")
    transpose.append(_sub("chromatic", "-2"))
    attrs.append(transpose)

    state_on = VoiceTimelineState(current_transpose=0.0)
    begin_measure(_measure(attrs), state_on, apply_musicxml_transpose=True)
    assert state_on.current_transpose == pytest.approx(-2.0)

    state_off = VoiceTimelineState(current_transpose=5.0)
    begin_measure(_measure(attrs), state_off, apply_musicxml_transpose=False)
    assert state_off.current_transpose == 5.0


def test_handle_backup_or_forward_backup_valid_moves_cursor_back_not_below_zero():
    state = VoiceTimelineState(current_divisions=4, cursor_time=2.0)
    backup = ET.Element("backup")
    backup.append(_sub("duration", "4"))
    assert handle_backup_or_forward(backup, state) is True
    assert state.cursor_time == pytest.approx(1.0)

    state_low = VoiceTimelineState(current_divisions=4, cursor_time=0.5)
    backup_big = ET.Element("backup")
    backup_big.append(_sub("duration", "8"))
    assert handle_backup_or_forward(backup_big, state_low) is True
    assert state_low.cursor_time == 0.0


def test_handle_backup_or_forward_backup_invalid_duration_is_noop():
    state = VoiceTimelineState(current_divisions=4, cursor_time=2.0)
    backup = ET.Element("backup")
    backup.append(_sub("duration", "bad"))
    assert handle_backup_or_forward(backup, state) is True
    assert state.cursor_time == pytest.approx(2.0)


def test_handle_backup_or_forward_forward_valid_advances_cursor():
    state = VoiceTimelineState(current_divisions=4, cursor_time=1.0)
    forward = ET.Element("forward")
    forward.append(_sub("duration", "8"))
    assert handle_backup_or_forward(forward, state) is True
    assert state.cursor_time == pytest.approx(3.0)


def test_handle_backup_or_forward_forward_invalid_duration_is_noop():
    state = VoiceTimelineState(current_divisions=4, cursor_time=1.0)
    forward = ET.Element("forward")
    forward.append(_sub("duration", "n/a"))
    assert handle_backup_or_forward(forward, state) is True
    assert state.cursor_time == pytest.approx(1.0)


def test_handle_backup_or_forward_unrelated_element_returns_false():
    state = VoiceTimelineState(current_divisions=4, cursor_time=1.25)
    note = ET.Element("note")
    note.append(_sub("pitch"))
    assert handle_backup_or_forward(note, state) is False
    assert state.cursor_time == pytest.approx(1.25)


@pytest.mark.parametrize(
    ("note_xml", "expected"),
    [
        ("<note><pitch/></note>", ("_global", "1")),
        ("<note><voice>2</voice><staff>1</staff><pitch/></note>", ("2", "1")),
        ("<note><voice> </voice><staff></staff><pitch/></note>", ("_global", "1")),
    ],
)
def test_voice_and_staff_keys(note_xml: str, expected: tuple[str, str]):
    note = ET.fromstring(note_xml)
    assert voice_and_staff_keys(note) == expected


@pytest.mark.parametrize(
    ("duration_text", "divisions", "expected"),
    [
        ("8", 4, 2.0),
        (None, 4, 0.0),
        ("bad", 4, 0.0),
        ("4", 0, 0.0),
    ],
)
def test_quarter_duration_for_note(duration_text, divisions, expected):
    note = ET.Element("note")
    if duration_text is not None:
        note.append(_sub("duration", duration_text))
    assert quarter_duration_for_note(note, divisions) == pytest.approx(expected)
