"""Onset-time verticality slices (simultaneities by score time)."""

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
from ._xml_primitives import (
    extract_pitch_from_note,
    find_child_by_suffix,
    tie_types_from_note,
)


def _parse_musicxml_verticalities_impl(
    file_bytes, include_grace: bool, include_cue: bool, *, apply_musicxml_transpose: bool
):
    xml_bytes = get_musicxml_bytes(file_bytes)
    if xml_bytes is None:
        return [], 0
    root = ET.fromstring(xml_bytes)
    verticalities: Dict[float, List[Tuple[str, float, int]]] = {}
    skipped_microtonal = 0

    for part in root.iter():
        if not part.tag.endswith("part"):
            continue
        state = VoiceTimelineState()
        reset_timeline_for_new_part(state)
        for measure in part:
            if not measure.tag.endswith("measure"):
                continue
            begin_measure(measure, state, apply_musicxml_transpose=apply_musicxml_transpose)

            for elem in measure:
                if handle_backup_or_forward(elem, state):
                    continue
                if not elem.tag.endswith("note"):
                    continue

                voice_key, _staff_key = voice_and_staff_keys(elem)
                duration = quarter_duration_for_note(elem, state.current_divisions)
                is_chord = find_child_by_suffix(elem, "chord") is not None
                has_grace = find_child_by_suffix(elem, "grace") is not None
                has_cue = find_child_by_suffix(elem, "cue") is not None
                tie_types = tie_types_from_note(elem)
                tie_stop_only = (
                    "stop" in tie_types or "continue" in tie_types
                ) and "start" not in tie_types

                onset = onset_quarters_for_note(state, voice_key, is_chord)

                if (
                    not tie_stop_only
                    and (include_grace or not has_grace)
                    and (include_cue or not has_cue)
                ):
                    note_tuple, skipped = extract_pitch_from_note(elem, state.current_transpose)
                    skipped_microtonal += skipped
                    if note_tuple is not None:
                        verticalities.setdefault(onset, []).append(note_tuple)

                advance_voice_after_note(state, voice_key, is_chord, duration)

            end_measure_advance_part_offset(state)

    slices = [{"time": t, "notes": verticalities[t]} for t in sorted(verticalities)]
    return slices, skipped_microtonal


def parse_musicxml_verticalities_bytes(file_bytes, include_grace: bool, include_cue: bool):
    """Onset verticalities using written ``<pitch>`` only (no ``<transpose>``)."""
    return _parse_musicxml_verticalities_impl(
        file_bytes, include_grace, include_cue, apply_musicxml_transpose=False
    )


def parse_musicxml_verticalities_bytes_with_sounding_transpose(
    file_bytes, include_grace: bool, include_cue: bool
):
    """Like ``parse_musicxml_verticalities_bytes`` but applies ``<transpose>`` (tests / advanced)."""
    return _parse_musicxml_verticalities_impl(
        file_bytes, include_grace, include_cue, apply_musicxml_transpose=True
    )
