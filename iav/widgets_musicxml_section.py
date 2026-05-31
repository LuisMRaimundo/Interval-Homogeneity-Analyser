"""MusicXML upload and slice-related controls."""

from __future__ import annotations

from typing import Any, Optional, Tuple

import streamlit as st

from iav.analysis_enums import MusicXmlImportMode, VerticalitySliceMode
from iav.analysis_presets import (
    KEY_APPLY_SOUNDING_TRANSPOSE,
    KEY_INCLUDE_CUE,
    KEY_INCLUDE_GRACE,
    KEY_MERGE_MANUAL,
    KEY_MIN_SLICE_NOTES,
    KEY_SLICE_MODE,
    KEY_XML_MODE,
)
from iav.interval_analysis_core import normalize_manual_notes


def render_musicxml_section(
    data: Any,
) -> Tuple[
    Optional[Any],
    MusicXmlImportMode,
    int,
    bool,
    bool,
    VerticalitySliceMode,
    bool,
    bool,
]:
    with st.expander("MusicXML upload"):
        uploaded = st.file_uploader(
            "Upload MusicXML (.xml, .musicxml, .mxl)",
            type=["xml", "musicxml", "mxl"],
            help=(
                "By default, pitches follow written <pitch> in the file. Enable "
                "**Apply MusicXML transposition (concert pitch)** below for transposing instruments."
            ),
        )
        xml_mode_raw = st.radio(
            "Import mode",
            options=[m.value for m in MusicXmlImportMode],
            horizontal=True,
            key=KEY_XML_MODE,
            help=(
                "Aggregate treats the whole file as one note collection. "
                "Verticalities extract simultaneities by onset time. "
                "Sounding verticalities track active-note sets over time."
            ),
        )
        xml_mode = MusicXmlImportMode(xml_mode_raw)
        apply_sounding_transpose = st.checkbox(
            "Apply MusicXML transposition (concert pitch)",
            key=KEY_APPLY_SOUNDING_TRANSPOSE,
            help=(
                "When checked, each measure's <transpose> chromatic shift is applied before "
                "interval analysis (Bb clarinet in written C becomes sounding D, etc.). "
                "When unchecked, <pitch> is read as written (default)."
            ),
        )
        if uploaded is not None and not apply_sounding_transpose:
            st.caption(
                "Written pitch mode: <transpose> is ignored. Check the box above for concert pitch."
            )
        min_slice_notes = st.slider(
            "Minimum notes per slice",
            min_value=1,
            max_value=8,
            step=1,
            key=KEY_MIN_SLICE_NOTES,
            help="Filter slices with too few notes when using Verticalities.",
        )
        include_grace_notes = st.checkbox(
            "Include grace notes (onset verticalities only)",
            key=KEY_INCLUDE_GRACE,
            help="Grace notes have no duration; they appear in onset slices only.",
        )
        include_cue_notes = st.checkbox(
            "Include cue notes (onset verticalities only)",
            key=KEY_INCLUDE_CUE,
            help="Cue notes are often editorial; exclude by default.",
        )
        st.caption("Sounding verticalities require duration > 0 and ignore grace notes.")
        slice_mode_raw = st.radio(
            "Verticality analysis",
            options=[m.value for m in VerticalitySliceMode],
            horizontal=True,
            key=KEY_SLICE_MODE,
            help="Choose how to analyze extracted slices for Verticalities modes.",
        )
        slice_mode = VerticalitySliceMode(slice_mode_raw)

        merge_manual = False
        if uploaded is not None:
            manual_parsed, _ = normalize_manual_notes(data)
            if len(manual_parsed) > 0:
                merge_manual = st.checkbox(
                    "Include manual notes in analysis",
                    key=KEY_MERGE_MANUAL,
                    help=(
                        "When off (default), only pitches from the uploaded file are analyzed; "
                        "the manual table is ignored. Turn on to combine both sources."
                    ),
                )

    return (
        uploaded,
        xml_mode,
        min_slice_notes,
        include_grace_notes,
        include_cue_notes,
        slice_mode,
        merge_manual,
        bool(st.session_state.get(KEY_APPLY_SOUNDING_TRANSPOSE, False)),
    )
