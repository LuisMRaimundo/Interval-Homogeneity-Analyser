"""Preset selector and apply button (uses iav.analysis_presets)."""

from __future__ import annotations

import streamlit as st

from iav.analysis_presets import (
    KEY_AUTO_APPLY,
    KEY_PRESET_CHOICE,
    PRESET_DESCRIPTIONS,
    PRESET_LABELS,
    AnalysisPresetId,
    apply_preset_to_session,
    ensure_widget_defaults,
)


def _apply_and_rerun() -> None:
    choice = st.session_state.get(KEY_PRESET_CHOICE, AnalysisPresetId.MANUAL_SINGLE_CHORD.value)
    apply_preset_to_session(choice)
    st.session_state["iav_preset_last_applied"] = choice


def _on_preset_select_change() -> None:
    if st.session_state.get(KEY_AUTO_APPLY):
        _apply_and_rerun()


def _on_auto_apply_toggle() -> None:
    if st.session_state.get(KEY_AUTO_APPLY):
        _apply_and_rerun()


def render_preset_controls() -> None:
    """Render preset UI; call once before other widgets (same run order)."""
    ensure_widget_defaults()
    choice = st.session_state.get(KEY_PRESET_CHOICE, AnalysisPresetId.MANUAL_SINGLE_CHORD.value)
    if st.session_state.get(KEY_AUTO_APPLY, True):
        last = st.session_state.get("iav_preset_last_applied")
        if last != choice:
            apply_preset_to_session(choice)
            st.session_state["iav_preset_last_applied"] = choice
    elif "iav_preset_last_applied" not in st.session_state:
        apply_preset_to_session(choice)
        st.session_state["iav_preset_last_applied"] = choice

    with st.expander("Analysis presets", expanded=False):
        st.caption(
            "Pick the situation that matches your score, click **Apply preset now**, "
            "then enter notes or upload MusicXML. Details: **ANALYSIS_PRESET.md**."
        )
        preset_ids = list(AnalysisPresetId)
        st.selectbox(
            "What are you analysing?",
            options=[p.value for p in preset_ids],
            format_func=lambda v: PRESET_LABELS[AnalysisPresetId(v)],
            key=KEY_PRESET_CHOICE,
            on_change=_on_preset_select_change,
            help=(
                "①–③ give one homogeneity value H. "
                "④ gives many H values over time (chart + CSV)."
            ),
        )
        choice = st.session_state.get(
            KEY_PRESET_CHOICE, AnalysisPresetId.MANUAL_SINGLE_CHORD.value
        )
        st.markdown(PRESET_DESCRIPTIONS[AnalysisPresetId(choice)])
        col_a, col_b = st.columns(2)
        with col_a:
            st.button(
                "Apply preset now",
                type="primary",
                width="stretch",
                on_click=_apply_and_rerun,
            )
        with col_b:
            st.checkbox(
                "Automatically apply selected preset",
                key=KEY_AUTO_APPLY,
                on_change=_on_auto_apply_toggle,
                help=(
                    "When enabled, changing the preset above or loading the app "
                    "applies that preset immediately (page reruns)."
                ),
            )
