"""Fixed analysis presets (values match ANALYSIS_PRESET.md and Streamlit widget keys)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, MutableMapping, cast

from iav.analysis_enums import (
    AnalysisThresholdMode,
    IntervallicHeadlineMode,
    MusicXmlImportMode,
    VerticalitySliceMode,
)

# Session-state keys (must match widgets_* key= arguments)
KEY_REMOVE_DUPLICATES = "iav_remove_duplicates"
KEY_EDO = "iav_edo"
KEY_THRESHOLD_MODE = "iav_threshold_mode"
KEY_HOMOGENEITY_SCORING = "iav_homogeneity_scoring"
KEY_HEADLINE_METRIC = "iav_headline_metric"
KEY_ALPHA_BASE = "iav_alpha_base"
KEY_AUTO_ALPHA = "iav_auto_alpha"
KEY_K_AUTO = "iav_k_auto"
KEY_XML_MODE = "iav_xml_mode"
KEY_MIN_SLICE_NOTES = "iav_min_slice_notes"
KEY_INCLUDE_GRACE = "iav_include_grace_notes"
KEY_INCLUDE_CUE = "iav_include_cue_notes"
KEY_SLICE_MODE = "iav_slice_mode"
KEY_MERGE_MANUAL = "iav_merge_manual"
KEY_APPLY_SOUNDING_TRANSPOSE = "iav_apply_sounding_transpose"

KEY_PRESET_CHOICE = "iav_preset_choice"
KEY_AUTO_APPLY = "iav_auto_apply_preset"

HOMOGENEITY_DOMINANCE_LABEL = "Dominance (max share)"
# Presets and first load: comparable aggregate H across examples (see ANALYSIS_PRESET.md).
HEADLINE_DEFAULT = IntervallicHeadlineMode.PAIRWISE


class AnalysisPresetId(str, Enum):
    MANUAL_SINGLE_CHORD = "manual_single_chord"
    MUSICXML_SINGLE_CHORD_ONSET = "musicxml_single_chord_onset"
    MUSICXML_SINGLE_CHORD_SOUNDING = "musicxml_single_chord_sounding"
    MUSICXML_ACTIVE_FRAGMENT = "musicxml_active_fragment"


# Short titles in the "Analysis preset" dropdown (plain language first).
PRESET_LABELS: dict[AnalysisPresetId, str] = {
    AnalysisPresetId.MANUAL_SINGLE_CHORD: (
        "① One chord — I type the notes (Manual input)"
    ),
    AnalysisPresetId.MUSICXML_SINGLE_CHORD_ONSET: (
        "② One chord from a score — at one attack time"
    ),
    AnalysisPresetId.MUSICXML_SINGLE_CHORD_SOUNDING: (
        "③ One sustained chord from a score — while notes are held"
    ),
    AnalysisPresetId.MUSICXML_ACTIVE_FRAGMENT: (
        "④ Passage with many chords — H changes over time"
    ),
}

# Shown under the dropdown after a preset is selected.
PRESET_DESCRIPTIONS: dict[AnalysisPresetId, str] = {
    AnalysisPresetId.MANUAL_SINGLE_CHORD: (
        "**You get:** one homogeneity **H** and **Interval heterogeneity (1 − H)** on the main results page.  \n"
        "**You do:** enter notes in **Manual input** (e.g. C4, E4, G4). Do not upload MusicXML.  \n"
        "**Settings applied:** **Fixed thresholds (heuristic)**, **Dominance (max share)**, "
        "**Pairwise intervallic concentration** as headline **H**. "
        "Adjacent regularity and hybrid (optional α) stay in **Intervallic metric suite**."
    ),
    AnalysisPresetId.MUSICXML_SINGLE_CHORD_ONSET: (
        "**You get:** one **H** for the chord you select.  \n"
        "**You do:** upload MusicXML, then pick the slice in **Choose slice to analyze**.  \n"
        "**Settings applied:** **Import mode** = **Verticalities (onset slices)**; "
        "**Verticality analysis** = **Single slice**; same homogeneity block as ①."
    ),
    AnalysisPresetId.MUSICXML_SINGLE_CHORD_SOUNDING: (
        "**You get:** one **H** for one sounding moment (ties / held notes).  \n"
        "**You do:** upload MusicXML, then pick the slice in **Choose slice to analyze**.  \n"
        "**Settings applied:** **Import mode** = **Sounding verticalities**; "
        "**Verticality analysis** = **Single slice**; same homogeneity block as ①."
    ),
    AnalysisPresetId.MUSICXML_ACTIVE_FRAGMENT: (
        "**You get:** **H** for each chord moment, **H-over-time** and **vertical note-count** charts, "
        "**slice_summary.csv**, and **vertical_cardinality_profile.json**.  \n"
        "**You do:** upload a trimmed excerpt, apply preset, then set **Select time window (quarter units)**.  \n"
        "**Settings applied:** **Verticalities (onset slices)** + **Time window (summary)**; "
        "**Minimum notes per slice** = 3. Not for a single H for the whole passage."
    ),
}


def _shared_analysis_values() -> dict[str, Any]:
    return {
        KEY_REMOVE_DUPLICATES: True,
        KEY_EDO: 12,
        KEY_THRESHOLD_MODE: AnalysisThresholdMode.FIXED_HEURISTIC.value,
        KEY_HOMOGENEITY_SCORING: HOMOGENEITY_DOMINANCE_LABEL,
        KEY_HEADLINE_METRIC: HEADLINE_DEFAULT,
        KEY_ALPHA_BASE: 0.55,
        KEY_AUTO_ALPHA: False,
        KEY_K_AUTO: 4,
    }


def _musicxml_slice_values(
    *,
    xml_mode: MusicXmlImportMode,
    slice_mode: VerticalitySliceMode,
    min_slice_notes: int,
) -> dict[str, Any]:
    return {
        KEY_XML_MODE: xml_mode.value,
        KEY_MIN_SLICE_NOTES: min_slice_notes,
        KEY_INCLUDE_GRACE: False,
        KEY_INCLUDE_CUE: False,
        KEY_SLICE_MODE: slice_mode.value,
        KEY_MERGE_MANUAL: False,
        KEY_APPLY_SOUNDING_TRANSPOSE: False,
    }


def _musicxml_idle_values() -> dict[str, Any]:
    """Safe MusicXML controls when not using passage batch mode (preset ① / manual)."""
    return {
        KEY_XML_MODE: MusicXmlImportMode.AGGREGATE.value,
        KEY_MIN_SLICE_NOTES: 2,
        KEY_INCLUDE_GRACE: True,
        KEY_INCLUDE_CUE: False,
        KEY_SLICE_MODE: VerticalitySliceMode.SINGLE.value,
        KEY_MERGE_MANUAL: False,
        KEY_APPLY_SOUNDING_TRANSPOSE: False,
    }


def preset_session_values(preset_id: AnalysisPresetId) -> dict[str, Any]:
    values = _shared_analysis_values()
    if preset_id == AnalysisPresetId.MANUAL_SINGLE_CHORD:
        values.update(_musicxml_idle_values())
        return values
    if preset_id == AnalysisPresetId.MUSICXML_ACTIVE_FRAGMENT:
        values.update(
            _musicxml_slice_values(
                xml_mode=MusicXmlImportMode.ONSET_VERTICALITIES,
                slice_mode=VerticalitySliceMode.TIME_WINDOW,
                min_slice_notes=3,
            )
        )
        return values
    xml_mode = (
        MusicXmlImportMode.SOUNDING_VERTICALITIES
        if preset_id == AnalysisPresetId.MUSICXML_SINGLE_CHORD_SOUNDING
        else MusicXmlImportMode.ONSET_VERTICALITIES
    )
    values.update(
        _musicxml_slice_values(
            xml_mode=xml_mode,
            slice_mode=VerticalitySliceMode.SINGLE,
            min_slice_notes=2,
        )
    )
    return values


# First-load widget seeds (= preset ①). Do not pass `value=`/`index=` on keyed widgets.
WIDGET_DEFAULTS: dict[str, Any] = {
    **_shared_analysis_values(),
    **_musicxml_idle_values(),
    KEY_PRESET_CHOICE: AnalysisPresetId.MANUAL_SINGLE_CHORD.value,
    KEY_AUTO_APPLY: True,
}


def ensure_widget_defaults(session: MutableMapping[str, Any] | None = None) -> None:
    """Seed session state for keyed widgets (only keys not already set)."""
    target: MutableMapping[str, Any] = cast(
        MutableMapping[str, Any],
        session if session is not None else __import__("streamlit").session_state,
    )
    for key, value in WIDGET_DEFAULTS.items():
        if key not in target:
            target[key] = value


def apply_preset_to_session(
    preset_id: AnalysisPresetId | str,
    session: MutableMapping[str, Any] | None = None,
) -> None:
    """Write preset widget values into Streamlit session state."""
    if isinstance(preset_id, str):
        preset_id = AnalysisPresetId(preset_id)
    target: MutableMapping[str, Any] = cast(
        MutableMapping[str, Any],
        session if session is not None else __import__("streamlit").session_state,
    )
    ensure_widget_defaults(target)
    for key, value in preset_session_values(preset_id).items():
        target[key] = value
