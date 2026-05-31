"""Streamlit widgets for analysis controls (manual table, MusicXML, EDO, homogeneity)."""

from __future__ import annotations

from iav.widget_state import WidgetState
from iav.widgets_analysis_section import render_analysis_section
from iav.widgets_manual_section import render_manual_section
from iav.widgets_musicxml_section import render_musicxml_section
from iav.widgets_presets import render_preset_controls


def render_all_widgets() -> WidgetState:
    render_preset_controls()
    data = render_manual_section()
    (
        uploaded,
        xml_mode,
        min_slice_notes,
        include_grace_notes,
        include_cue_notes,
        slice_mode,
        merge_manual,
        apply_sounding_transpose,
    ) = render_musicxml_section(data)
    (
        remove_duplicates,
        edo,
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
    ) = render_analysis_section()

    return WidgetState(
        data=data,
        uploaded=uploaded,
        xml_mode=xml_mode,
        min_slice_notes=min_slice_notes,
        include_grace_notes=include_grace_notes,
        include_cue_notes=include_cue_notes,
        slice_mode=slice_mode,
        remove_duplicates=remove_duplicates,
        edo=int(edo),
        bin_cents=bin_cents,
        mode=mode,
        dominance_threshold=dominance_threshold,
        even_high=even_high,
        even_low=even_low,
        chain_threshold=chain_threshold,
        homogeneity_method=homogeneity_method,
        score_label=score_label,
        intervallic_headline_mode=intervallic_headline_mode,
        alpha_base=alpha_base,
        auto_alpha=auto_alpha,
        k_auto=k_auto,
        merge_manual=merge_manual,
        apply_sounding_transpose=apply_sounding_transpose,
    )


__all__ = ["WidgetState", "render_all_widgets"]
