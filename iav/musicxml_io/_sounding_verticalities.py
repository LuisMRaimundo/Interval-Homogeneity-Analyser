"""Sounding verticalities: active-note sets between score times (duration + ties)."""

from __future__ import annotations

from typing import Dict, List, Tuple

from defusedxml import ElementTree as ET

from ._flat_score import get_musicxml_bytes
from ._measure_voice_cursor import (
    VoiceTimelineState,
    advance_voice_after_note,
    begin_measure,
    end_measure_advance_part_offset,
    handle_backup_or_forward,
    onset_quarters_for_note,
    quarter_duration_for_note,
    reset_timeline_for_new_part,
    voice_and_staff_keys,
)
from ._xml_primitives import extract_pitch_from_note, find_child_by_suffix, tie_types_from_note


def _parse_musicxml_sounding_verticalities_impl(file_bytes, *, apply_musicxml_transpose: bool):
    xml_bytes = get_musicxml_bytes(file_bytes)
    if xml_bytes is None:
        return [], 0
    root = ET.fromstring(xml_bytes)
    Note3 = Tuple[str, float, int]
    events: Dict[float, List[Tuple[Note3, int]]] = {}
    skipped_microtonal = 0

    for part in root.iter():
        if not part.tag.endswith("part"):
            continue
        part_id = part.attrib.get("id", "part")
        state = VoiceTimelineState()
        reset_timeline_for_new_part(state)
        open_ties: Dict[Tuple[str, str, str, Note3], Dict[str, float]] = {}

        for measure in part:
            if not measure.tag.endswith("measure"):
                continue
            begin_measure(measure, state, apply_musicxml_transpose=apply_musicxml_transpose)

            for elem in measure:
                if handle_backup_or_forward(elem, state):
                    continue
                if not elem.tag.endswith("note"):
                    continue

                voice_key, staff_key = voice_and_staff_keys(elem)
                duration = quarter_duration_for_note(elem, state.current_divisions)
                is_chord = find_child_by_suffix(elem, "chord") is not None
                tie_types = tie_types_from_note(elem)

                onset = onset_quarters_for_note(state, voice_key, is_chord)

                note_tuple, skipped = extract_pitch_from_note(elem, state.current_transpose)
                skipped_microtonal += skipped
                if note_tuple is not None:
                    note = note_tuple
                    if duration > 0:
                        start = onset
                        end = onset + duration
                        tie_key = (part_id, staff_key, voice_key, note)
                        tie_has_start = "start" in tie_types
                        tie_has_stop = "stop" in tie_types
                        tie_has_continue = "continue" in tie_types
                        if tie_has_start or tie_has_stop or tie_has_continue:
                            if tie_key in open_ties:
                                open_ties[tie_key]["end"] = max(open_ties[tie_key]["end"], end)
                            else:
                                if tie_has_start:
                                    events.setdefault(start, []).append((note, 1))
                                    open_ties[tie_key] = {"end": end}
                                else:
                                    events.setdefault(start, []).append((note, 1))
                                    events.setdefault(end, []).append((note, -1))
                                    continue
                            if tie_has_stop and not tie_has_start and tie_key in open_ties:
                                tie_range = open_ties.pop(tie_key)
                                events.setdefault(tie_range["end"], []).append((note, -1))
                        else:
                            events.setdefault(start, []).append((note, 1))
                            events.setdefault(end, []).append((note, -1))

                advance_voice_after_note(state, voice_key, is_chord, duration)

            end_measure_advance_part_offset(state)

        for tie_key, tie_range in open_ties.items():
            events.setdefault(tie_range["end"], []).append((tie_key[3], -1))

    if not events:
        return [], skipped_microtonal

    times = sorted(events.keys())
    active_counts: Dict[Note3, int] = {}
    slices = []
    for idx, t in enumerate(times):
        deltas = sorted(events[t], key=lambda item: item[1])
        for note, delta in deltas:
            active_counts[note] = active_counts.get(note, 0) + delta
            if active_counts[note] <= 0:
                del active_counts[note]
        if idx + 1 < len(times):
            t_next = times[idx + 1]
            if t_next > t and active_counts:
                notes = []
                for note, count in active_counts.items():
                    notes.extend([note] * count)
                slices.append({"start": t, "end": t_next, "notes": notes})
    return slices, skipped_microtonal


def parse_musicxml_sounding_verticalities_bytes(file_bytes):
    """Sounding verticalities using written ``<pitch>`` only (no ``<transpose>``)."""
    return _parse_musicxml_sounding_verticalities_impl(file_bytes, apply_musicxml_transpose=False)


def parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose(file_bytes):
    """Like ``parse_musicxml_sounding_verticalities_bytes`` but applies ``<transpose>`` (tests / advanced)."""
    return _parse_musicxml_sounding_verticalities_impl(file_bytes, apply_musicxml_transpose=True)
