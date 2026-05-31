"""
Shared MusicXML timeline logic: divisions, per-measure voice times, backup/forward, onset grid.

Both onset verticalities and sounding verticalities walk each ``<part>`` the same way for
``<measure>`` children: read the first ``<attributes>`` on the measure (divisions / transpose),
reset voice-relative clocks, then stream ``<backup>``, ``<forward>``, and ``<note>`` events.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._xml_primitives import find_child_by_suffix, transpose_from_attributes


@dataclass
class VoiceTimelineState:
    """Running quarter-note grid for one ``<part>`` (MusicXML ``<divisions>`` units)."""

    measure_offset: float = 0.0
    current_divisions: int = 1
    current_transpose: float = 0.0
    voice_time: dict[str, float] = field(default_factory=dict)
    last_onset: dict[str, float] = field(default_factory=dict)
    cursor_time: float = 0.0


def reset_timeline_for_new_part(state: VoiceTimelineState) -> None:
    state.measure_offset = 0.0
    state.current_divisions = 1
    state.current_transpose = 0.0


def begin_measure(
    measure,
    state: VoiceTimelineState,
    *,
    apply_musicxml_transpose: bool,
) -> None:
    """Clear per-measure voice maps and apply the first ``<attributes>`` on this measure."""
    state.voice_time.clear()
    state.last_onset.clear()
    state.cursor_time = 0.0
    attributes = find_child_by_suffix(measure, "attributes")
    if attributes is None:
        return
    divisions_elem = find_child_by_suffix(attributes, "divisions")
    if divisions_elem is not None and divisions_elem.text:
        try:
            state.current_divisions = int(divisions_elem.text)
        except (TypeError, ValueError):
            state.current_divisions = state.current_divisions or 1
    if apply_musicxml_transpose:
        state.current_transpose = transpose_from_attributes(attributes)


def handle_backup_or_forward(measure_event, state: VoiceTimelineState) -> bool:
    """
    If ``measure_event`` is ``<backup>`` or ``<forward>``, adjust ``cursor_time`` and return True.
    Otherwise return False.
    """
    if measure_event.tag.endswith("backup"):
        dur = find_child_by_suffix(measure_event, "duration")
        if dur is not None:
            try:
                state.cursor_time = max(
                    0.0,
                    state.cursor_time - (int(dur.text) / float(state.current_divisions)),
                )
            except (TypeError, ValueError):
                pass
        return True
    if measure_event.tag.endswith("forward"):
        dur = find_child_by_suffix(measure_event, "duration")
        if dur is not None:
            try:
                state.cursor_time += int(dur.text) / float(state.current_divisions)
            except (TypeError, ValueError):
                pass
        return True
    return False


def voice_and_staff_keys(note_elem) -> tuple[str, str]:
    """``voice_key`` (``_global`` if absent) and ``staff_key`` (``\"1\"`` if absent)."""
    voice_elem = find_child_by_suffix(note_elem, "voice")
    voice = voice_elem.text.strip() if voice_elem is not None and voice_elem.text else None
    voice_key = voice or "_global"
    staff_elem = find_child_by_suffix(note_elem, "staff")
    staff = staff_elem.text.strip() if staff_elem is not None and staff_elem.text else None
    staff_key = staff or "1"
    return voice_key, staff_key


def quarter_duration_for_note(note_elem, divisions: int) -> float:
    duration_elem = find_child_by_suffix(note_elem, "duration")
    try:
        raw_duration = int(duration_elem.text) if duration_elem is not None else 0
    except (TypeError, ValueError):
        raw_duration = 0
    return raw_duration / float(divisions) if divisions else 0.0


def onset_quarters_for_note(state: VoiceTimelineState, voice_key: str, is_chord: bool) -> float:
    """Absolute onset in quarter-note units from the start of the current ``<part>``."""
    if voice_key not in state.voice_time:
        state.voice_time[voice_key] = state.cursor_time
    if is_chord and voice_key in state.last_onset:
        return state.last_onset[voice_key]
    onset = state.measure_offset + state.voice_time[voice_key]
    state.last_onset[voice_key] = onset
    return onset


def advance_voice_after_note(
    state: VoiceTimelineState,
    voice_key: str,
    is_chord: bool,
    duration_quarters: float,
) -> None:
    if not is_chord:
        state.voice_time[voice_key] += duration_quarters
        if voice_key == "_global":
            state.cursor_time = state.voice_time[voice_key]


def end_measure_advance_part_offset(state: VoiceTimelineState) -> None:
    if state.voice_time:
        state.measure_offset += max(state.voice_time.values())
