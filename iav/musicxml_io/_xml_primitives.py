"""Low-level MusicXML element helpers (pitch, ties, transposition)."""

from __future__ import annotations

from iav.pitch_model import (
    ACCIDENTAL_TOKENS,
    MICROTONAL_ACCIDENTALS,
    NOTE_BASE,
    chromatic_midi_float,
    spelled_note_from_chromatic_midi,
)


def find_child_by_suffix(node, suffix):
    for child in node:
        if child.tag.endswith(suffix):
            return child
    return None


def extract_pitch_from_note(note_elem, transpose_semitones: float = 0.0):
    pitch = find_child_by_suffix(note_elem, "pitch")
    if pitch is None:
        return None, 0

    step = find_child_by_suffix(pitch, "step")
    octave = find_child_by_suffix(pitch, "octave")
    alter = find_child_by_suffix(pitch, "alter")
    accidental = find_child_by_suffix(note_elem, "accidental")

    step_text = step.text if step is not None else None
    octave_text = octave.text if octave is not None else None
    alter_text = alter.text if alter is not None else None
    accidental_text = (
        accidental.text.strip().lower() if accidental is not None and accidental.text else None
    )

    if step_text is None or octave_text is None:
        return None, 0

    letter = step_text.strip().upper()
    if letter not in NOTE_BASE:
        return None, 0

    try:
        octave_value = int(octave_text)
    except ValueError:
        return None, 0

    alter_value = None
    if alter_text is not None:
        try:
            alter_value = float(alter_text)
        except ValueError:
            return None, 1

    if accidental_text is not None:
        if accidental_text not in ACCIDENTAL_TOKENS:
            return None, 1
        acc_val = ACCIDENTAL_TOKENS[accidental_text]
        if accidental_text in MICROTONAL_ACCIDENTALS:
            if alter_value is None or abs(alter_value) < 1e-12:
                alter_value = acc_val
        elif alter_value is None:
            alter_value = acc_val

    if alter_value is None:
        alter_value = 0.0

    t = float(transpose_semitones)
    if abs(t) > 1e-12:
        total_midi = chromatic_midi_float(letter, alter_value, octave_value) + t
        letter, alter_value, octave_value = spelled_note_from_chromatic_midi(total_midi)
    return (letter, alter_value, octave_value), 0


def tie_types_from_note(note_elem):
    tie_types = set()
    tie_elems = [c for c in note_elem if c.tag.endswith("tie")]
    tie_types.update(t.attrib.get("type") for t in tie_elems if t.attrib.get("type"))

    notations = find_child_by_suffix(note_elem, "notations")
    if notations is not None:
        for child in notations:
            if child.tag.endswith("tied"):
                t = child.attrib.get("type")
                if t:
                    tie_types.add(t)
    return tie_types


def transpose_from_attributes(attributes):
    if attributes is None:
        return 0.0
    transpose = find_child_by_suffix(attributes, "transpose")
    if transpose is None:
        return 0.0
    chromatic = find_child_by_suffix(transpose, "chromatic")
    octave_change = find_child_by_suffix(transpose, "octave-change")
    semitones = 0.0
    if chromatic is not None and chromatic.text:
        try:
            semitones += float(chromatic.text)
        except ValueError:
            pass
    if octave_change is not None and octave_change.text:
        try:
            semitones += 12.0 * float(octave_change.text)
        except ValueError:
            pass
    return semitones
