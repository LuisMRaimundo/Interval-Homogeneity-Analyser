"""Streamlit UI orchestration for Interval_Homogeneity (entry: app.py)."""

from __future__ import annotations

import streamlit as st

from iav.constants import MAX_NOTES
from iav.interval_analysis_core import (
    compute_alpha_used,
    metrics_for_notes,
    normalize_manual_notes,
)
from iav.musicxml import apply_dedupe_policy, ingest_musicxml
from iav.note_sources import assemble_notes_from_manual_and_xml
from iav.results import render_aggregate_results
from iav.symbolic_profile import intervallic_profile_for_notes
from iav.widgets import render_all_widgets


def render_analysis() -> None:
    w = render_all_widgets()

    raw_data = w.data
    if raw_data is None:
        raw_data = []
    manual_notes, manual_errors = normalize_manual_notes(raw_data)

    skipped_microtonal_total = 0
    if w.uploaded is not None:
        xml_notes, skipped_microtonal_total = ingest_musicxml(w, [])
        notes = assemble_notes_from_manual_and_xml(manual_notes, xml_notes, True, w.merge_manual)
        if w.merge_manual and len(manual_notes) > 0:
            st.info(f"Merged {len(manual_notes)} manual notes with MusicXML input.")
    else:
        notes = list(manual_notes)

    if manual_errors:
        st.warning("\n".join(manual_errors))

    notes, deduplication_active = apply_dedupe_policy(w, notes)

    if skipped_microtonal_total > 0:
        st.info(f"Skipped {skipped_microtonal_total} notes with invalid alter values.")

    if len(notes) > MAX_NOTES:
        st.error(
            f"Too many notes for pairwise analysis ({len(notes)}). "
            f"Please reduce the input to {MAX_NOTES} notes or fewer."
        )
        st.stop()

    if len(notes) < 2:
        st.info("Add at least two notes to compute intervals.")
        st.stop()

    note_count = len(notes)
    alpha_used = compute_alpha_used(note_count, w.alpha_base, w.auto_alpha, w.k_auto)

    metrics = metrics_for_notes(
        notes,
        w.dominance_threshold,
        w.even_high,
        w.even_low,
        alpha_used,
        w.homogeneity_method,
        bin_cents=w.bin_cents,
        chain_threshold=w.chain_threshold,
        intervallic_headline_mode=w.intervallic_headline_mode,
    )

    intervallic = intervallic_profile_for_notes(
        notes,
        edo=w.edo,
        distance_counts=metrics["distance_counts"],
    )
    render_aggregate_results(
        w,
        notes,
        metrics,
        alpha_used,
        intervallic_profile=intervallic,
        deduplication_active=deduplication_active,
    )
