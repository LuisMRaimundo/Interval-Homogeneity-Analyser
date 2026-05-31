"""EDO / thresholds / homogeneity model controls."""

from __future__ import annotations

import streamlit as st

from iav.analysis_enums import (
    AnalysisThresholdMode,
    HomogeneityMethod,
    HomogeneityScoreKind,
    IntervallicHeadlineMode,
)
from iav.analysis_presets import (
    KEY_ALPHA_BASE,
    KEY_AUTO_ALPHA,
    KEY_EDO,
    KEY_HEADLINE_METRIC,
    KEY_HOMOGENEITY_SCORING,
    KEY_K_AUTO,
    KEY_REMOVE_DUPLICATES,
    KEY_THRESHOLD_MODE,
)
from iav.ui_params import (
    bin_cents_for_edo,
    homogeneity_method_from_ui_label,
    score_kind_for_homogeneity_method,
    threshold_tuple_for_mode,
)


def render_analysis_section() -> tuple[
    bool,
    int,
    int,
    AnalysisThresholdMode,
    float,
    float,
    float,
    float,
    HomogeneityMethod,
    HomogeneityScoreKind,
    IntervallicHeadlineMode,
    float,
    bool,
    int,
]:
    with st.expander("Data preparation"):
        remove_duplicates = st.checkbox(
            "Collapse to unique pitches (selected EDO grid)",
            key=KEY_REMOVE_DUPLICATES,
            help="Recommended for aggregates/chords; otherwise repeated notes inflate counts.",
        )

    st.subheader("Analysis mode")
    edo = st.selectbox(
        "Tuning system (EDO)",
        options=[12, 24, 48],
        key=KEY_EDO,
        help="Controls pitch quantization for intervals and deduplication.",
    )
    bin_cents = bin_cents_for_edo(int(edo))
    st.caption(f"Analysis grid: {bin_cents} cents per step.")

    mode_raw = st.radio(
        "Choose a mode",
        options=[m.value for m in AnalysisThresholdMode],
        horizontal=True,
        key=KEY_THRESHOLD_MODE,
        help=("Standard lets you tune thresholds. Fixed thresholds shows the rationale panel."),
    )
    mode = AnalysisThresholdMode(mode_raw)

    if mode == AnalysisThresholdMode.STANDARD:
        with st.expander("Labeling settings"):
            dominance_threshold = st.slider(
                "Dominant interval threshold (share of all pairwise intervals)",
                min_value=0.2,
                max_value=0.8,
                value=0.35,
                step=0.05,
            )
            even_high = st.slider(
                "Evenness high threshold",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                step=0.05,
            )
            even_low = st.slider(
                "Evenness low threshold",
                min_value=0.0,
                max_value=0.5,
                value=0.3,
                step=0.05,
            )
            chain_threshold = st.slider(
                "Chain regularity threshold",
                min_value=0.30,
                max_value=0.90,
                value=0.60,
                step=0.05,
                help=(
                    "Adjacent-interval (chain) dominance: ≥0.95 → uniform stacking; "
                    "≥ this threshold (and <0.95) → predominantly regular stacking; "
                    "below → irregular stacking."
                ),
            )
    else:
        dominance_threshold, even_high, even_low, chain_threshold = threshold_tuple_for_mode(mode)
        st.caption(
            "Fixed-threshold mode uses dominance ≥ 0.60, evenness ≥ 0.80 (high) and ≤ 0.30 (low)."
        )

    with st.expander("Homogeneity model settings", expanded=True):
        homogeneity_method_label = st.radio(
            "Homogeneity scoring",
            options=[
                "Dominance (max share)",
                "Entropy concentration (1 - entropy)",
                "Combined view (both + consensus)",
            ],
            horizontal=True,
            key=KEY_HOMOGENEITY_SCORING,
            help=(
                "Dominance = share of the most frequent interval type (blunt: e.g. chromatic "
                "clusters and whole-tone chains can share the same pairwise dominance). "
                "Entropy concentration uses the full distribution (span-normalised; see caption below). "
                "Combined view reports both and a consensus score."
            ),
        )
        homogeneity_method = homogeneity_method_from_ui_label(homogeneity_method_label)
        score_label = score_kind_for_homogeneity_method(homogeneity_method)
        _headline_labels = {
            IntervallicHeadlineMode.PAIRWISE: "Global pairwise concentration (default)",
            IntervallicHeadlineMode.ADJACENT: "Adjacent intervallic regularity",
            IntervallicHeadlineMode.WEIGHTED_LINEAR: "Proximity-weighted (1/|i−j|)",
            IntervallicHeadlineMode.WEIGHTED_QUADRATIC: "Proximity-weighted (1/|i−j|²)",
            IntervallicHeadlineMode.HYBRID: "Hybrid (α·adjacent + (1−α)·pairwise)",
        }
        headline_pick = st.radio(
            "Headline intervallic metric (H)",
            options=list(_headline_labels.keys()),
            format_func=lambda m: _headline_labels[m],
            key=KEY_HEADLINE_METRIC,
            help=(
                "All four constructions are always computed for comparison. This choice sets which "
                "one is shown as headline H and used for H_label / slice ΔH."
            ),
        )
        intervallic_headline_mode = headline_pick
        alpha_base = st.slider(
            "α — weight on adjacent in hybrid H",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            key=KEY_ALPHA_BASE,
            disabled=intervallic_headline_mode != IntervallicHeadlineMode.HYBRID,
            help=(
                "Hybrid: H = α·adjacent regularity + (1−α)·pairwise concentration. "
                "α = 0.6 favours local/generative repetition (e.g. chromatic clusters); "
                "α = 0.5 balances both; lower α keeps global pairwise emphasis."
            ),
        )
        auto_alpha = st.checkbox(
            "Auto-adjust α with note count (hybrid only)",
            key=KEY_AUTO_ALPHA,
            disabled=intervallic_headline_mode != IntervallicHeadlineMode.HYBRID,
            help="When on, effective α moves toward 1.0 as note count grows.",
        )
        k_auto = st.slider(
            "Auto-adjust strength (k)",
            min_value=1,
            max_value=12,
            step=1,
            key=KEY_K_AUTO,
            disabled=not (auto_alpha and intervallic_headline_mode == IntervallicHeadlineMode.HYBRID),
        )

        st.caption(
            "Presets use **pairwise** as headline **H** for comparable aggregates. "
            "Pairwise, adjacent, and proximity-weighted scores share the dominance or entropy path above. "
            "Entropy concentration normalizes by **ln(span+1)** in pitch-bin units (register span affects the ceiling). "
            "Hybrid **H** = α·adjacent + (1−α)·pairwise — report α if you switch to it. "
            "See sidebar: **Which metric to use?**"
        )

    return (
        remove_duplicates,
        int(edo),
        bin_cents,
        mode,
        dominance_threshold,
        even_high,
        even_low,
        chain_threshold,
        homogeneity_method,
        score_label,
        intervallic_headline_mode,
        alpha_base,
        auto_alpha,
        k_auto,
    )
