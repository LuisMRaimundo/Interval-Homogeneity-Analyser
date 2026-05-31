"""Aggregate summary, tables, and CSV export."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from iav.analysis_enums import (
    AnalysisThresholdMode,
    HomogeneityMethod,
    IntervallicHeadlineMode,
)
from iav.charts import render_visualization_section
from iav.interval_analysis_core import set_class_summary_12tet
from iav.results_aggregate_data import (
    adjacency_rows,
    analysis_csv_string,
    interval_label_rows,
    semi_distance_rows,
)
from iav.symbolic_profile import IntervallicProfile
from iav.vertical_cardinality import (
    build_vertical_cardinality_profile,
    vertical_cardinality_profile_json,
)
from iav.widget_state import WidgetState

NoteList = List[Any]


def _render_intervallic_supplement(
    w: WidgetState,
    intervallic: IntervallicProfile,
    pc_set_summary: Optional[Dict[str, Any]],
) -> None:
    st.subheader("Intervallic context (optional)")
    st.caption(
        "Pairwise interval homogeneity is in **H** and the tables below. "
        "This block adds mod-12 interval-class evenness and reference **interval** fingerprints only — "
        "not registral dispersion (use your separate tool for register layout)."
    )
    if w.edo == 12 and pc_set_summary is not None:
        st.write(f"**Interval vector** (ic1–ic6): {pc_set_summary['interval_vector_str']}")
        if intervallic.ic_evenness is not None:
            st.write(f"**IC evenness** (observed classes): **{intervallic.ic_evenness:.3f}**")
    elif w.edo != 12:
        st.caption("Mod-12 interval vector: select **12-EDO** in Analysis mode.")
    elif pc_set_summary is None:
        st.caption("Mod-12 tools need integral semitone spellings on each note.")

    if intervallic.reference_comparisons:
        st.markdown("**Reference interval fingerprints** (L1 on pairwise distance shares)")
        for ref_id, label, dist in intervallic.reference_comparisons:
            st.write(f"- {label} (`{ref_id}`): L1 = **{dist:.3f}**")


def render_aggregate_results(
    w: WidgetState,
    notes: NoteList,
    metrics: Dict[str, Any],
    alpha_used: float,
    *,
    intervallic_profile: Optional[IntervallicProfile] = None,
    deduplication_active: bool = False,
) -> None:
    interval_counts = metrics["interval_counts"]
    distance_counts = metrics["distance_counts"]
    adj_counts = metrics["adj_counts"]
    total_intervals = metrics["total_intervals"]
    type_score = metrics["type_score"]
    evenness_score = metrics["evenness_score"]
    classification = metrics["classification"]
    h_label = metrics["H_label"]
    compactness_score = metrics["compactness_score"]
    pitch_span = metrics["pitch_span"]
    avg_distance = metrics["avg_distance"]
    top_pair_label = metrics["top_pair_label"]
    top_pair_semi_count = metrics["top_pair_semi_count"]
    top_pair_semi_share = metrics["top_pair_semi_share"]
    top_chain_label = metrics["top_chain_label"]
    top_chain_semi_count = metrics["top_chain_semi_count"]
    top_chain_semi_share = metrics["top_chain_semi_share"]
    bin_cents = w.bin_cents
    note_count = len(notes)
    pc_set_summary = set_class_summary_12tet(notes) if w.edo == 12 else None

    st.subheader("Aggregate summary")
    st.write(f"Total notes (after preparation): {note_count}")
    st.write(f"Total pairwise intervals: {total_intervals}")
    st.write(f"Aggregate label (pairwise + chain): **{classification}**")
    st.write(f"H classification: **{h_label}**")

    st.write(f"Type concentration (pairwise, custom): **{type_score:.3f}**")
    evenness_title = metrics.get(
        "evenness_title",
        "Pairwise interval evenness (normalized Shannon entropy of label counts)",
    )
    st.write(f"{evenness_title}: **{evenness_score:.3f}**")

    if w.homogeneity_method == HomogeneityMethod.COMBINED:
        chain_dom = metrics["chain_dom"]
        pair_dom = metrics["pair_dom"]
        chain_ent = metrics["chain_ent"]
        pair_ent = metrics["pair_ent"]
        h_dom = metrics["H_dom"]
        h_ent = metrics["H_ent"]
        h_consensus = metrics["H_consensus"]

        st.write(f"Chain dominance (adjacent): **{chain_dom:.3f}**")
        st.write(f"Pairwise dominance: **{pair_dom:.3f}**")
        st.write(f"Chain concentration (adjacent): **{chain_ent:.3f}**")
        st.write(f"Pairwise concentration: **{pair_ent:.3f}**")
        if w.intervallic_headline_mode == IntervallicHeadlineMode.HYBRID:
            st.write(
                f"Alpha used in H: **{alpha_used:.3f}** (base={w.alpha_base:.2f}, auto={w.auto_alpha})"
            )
        else:
            st.caption(
                f"Headline H follows **{w.intervallic_headline_mode.value}**; α applies only in hybrid mode."
            )

        if top_chain_label is not None:
            st.write(
                f"Dominant adjacent interval: **{top_chain_label}** "
                f"({top_chain_semi_count} / {max(1, note_count - 1)}, {top_chain_semi_share:.1%})"
            )
        if top_pair_label is not None:
            st.write(
                f"Dominant pairwise interval: **{top_pair_label}** "
                f"({top_pair_semi_count} / {total_intervals}, {top_pair_semi_share:.1%})"
            )
    else:
        chain_score = metrics["chain_score"]
        pair_score = metrics["pair_score"]
        chain_title = metrics.get("chain_metric_title", f"Chain {w.score_label}")
        pair_title = metrics.get("pair_metric_title", f"Pairwise {w.score_label}")
        st.write(f"{chain_title} (adjacent): **{chain_score:.3f}**")
        if top_chain_label is not None:
            st.write(
                f"Dominant adjacent interval: **{top_chain_label}** "
                f"({top_chain_semi_count} / {max(1, note_count - 1)}, {top_chain_semi_share:.1%})"
            )

        st.write(f"{pair_title}: **{pair_score:.3f}**")
        if w.intervallic_headline_mode == IntervallicHeadlineMode.HYBRID:
            st.write(
                f"Alpha used in H: **{alpha_used:.3f}** (base={w.alpha_base:.2f}, auto={w.auto_alpha})"
            )
        else:
            st.caption(
                f"Headline H follows **{w.intervallic_headline_mode.value}**; α applies only in hybrid mode."
            )
        if top_pair_label is not None:
            st.write(
                f"Dominant pairwise interval: **{top_pair_label}** "
                f"({top_pair_semi_count} / {total_intervals}, {top_pair_semi_share:.1%})"
            )

    w_lin = metrics.get("weighted_linear_score")
    w_quad = metrics.get("weighted_quadratic_score")
    with st.expander("Intervallic metric suite (all constructions)", expanded=True):
        st.caption(
            "Four complementary views of the same aggregate. Headline **H** (below) follows your "
            f"selected mode: **{w.intervallic_headline_mode.value}**."
        )
        if w.homogeneity_method == HomogeneityMethod.COMBINED:
            st.write(
                f"- **Pairwise concentration** (dom / ent): "
                f"**{metrics['pair_dom']:.3f}** / **{metrics['pair_ent']:.3f}**"
            )
            st.write(
                f"- **Adjacent regularity** (dom / ent): "
                f"**{metrics['chain_dom']:.3f}** / **{metrics['chain_ent']:.3f}**"
            )
            if metrics.get("weighted_linear_dom") is not None:
                st.write(
                    f"- **Proximity-weighted 1/|i−j|** (dom / ent): "
                    f"**{metrics['weighted_linear_dom']:.3f}** / **{metrics['weighted_linear_ent']:.3f}**"
                )
                st.write(
                    f"- **Proximity-weighted 1/|i−j|²** (dom / ent): "
                    f"**{metrics['weighted_quadratic_dom']:.3f}** / **{metrics['weighted_quadratic_ent']:.3f}**"
                )
        else:
            st.write(f"- **Pairwise intervallic concentration:** **{metrics['pair_score']:.3f}**")
            st.write(f"- **Adjacent intervallic regularity:** **{metrics['chain_score']:.3f}**")
            if w_lin is not None and w_quad is not None:
                st.write(f"- **Proximity-weighted (1/|i−j|):** **{w_lin:.3f}**")
                st.write(f"- **Proximity-weighted (1/|i−j|²):** **{w_quad:.3f}**")
        if w.intervallic_headline_mode == IntervallicHeadlineMode.HYBRID:
            st.write(
                f"- **Hybrid** (α·adjacent + (1−α)·pairwise), α = **{alpha_used:.2f}**: "
                f"**{alpha_used * metrics['chain_score'] + (1 - alpha_used) * metrics['pair_score']:.3f}**"
            )

    st.subheader("Intervallic homogeneity (headline H)")
    h_primary_title = metrics.get("H_primary_title", "Intervallic homogeneity H")
    h_primary_help = metrics.get(
        "H_primary_help",
        "Concentration of unordered pairwise interval shares on the analysis grid (symbolic, not auditory).",
    )
    st.caption(f"{h_primary_title}. {h_primary_help}")
    if w.intervallic_headline_mode == IntervallicHeadlineMode.HYBRID:
        st.info(
            f"**Hybrid intervallic homogeneity:** "
            f"H = **{alpha_used:.3f}** × adjacent regularity + **{1 - alpha_used:.3f}** × pairwise concentration "
            f"(α_base = {w.alpha_base:.2f}, auto-adjust = {w.auto_alpha}). "
            "Cite this formula when reporting hybrid H."
        )
    elif w.intervallic_headline_mode == IntervallicHeadlineMode.ADJACENT:
        st.caption(
            "Headline H is **adjacent-step regularity**, not global pairwise homogeneity. "
            "See pairwise concentration in the metric suite for the unordered cloud."
        )
    if w.homogeneity_method == HomogeneityMethod.COMBINED:
        h_dom = metrics["H_dom"]
        h_ent = metrics["H_ent"]
        h_consensus = metrics["H_consensus"]
        h_main = h_consensus
        st.write(f"**H (dominance heuristic):** {h_dom:.3f}  ({h_dom * 100:.1f}/100)")
        st.write(f"**H (entropy concentration heuristic):** {h_ent:.3f}  ({h_ent * 100:.1f}/100)")
        st.write(
            f"**H (consensus, geometric mean):** {h_consensus:.3f}  ({h_consensus * 100:.1f}/100)"
        )
        st.write(
            f"**Interval heterogeneity (consensus):** {(1.0 - h_consensus) * 100:.1f}/100 (1 − H)"
        )
    else:
        h_main = metrics["H"]
        st.write(f"**{h_primary_title}:** {h_main:.3f}  ({h_main * 100:.1f}/100)")
        st.write(f"**Interval heterogeneity (1 − H):** {(1.0 - h_main) * 100:.1f}/100")
    st.slider(
        "Interval heterogeneity ←  |  homogeneity scale  |  → Homogeneity",
        min_value=0.0,
        max_value=1.0,
        value=float(h_main),
        step=0.01,
        disabled=True,
    )

    st.caption(
        "Note: interval labels here are pitch-distance labels (derived from the selected EDO grid). "
        "They are not spelling-aware (A4 vs d5 etc.)."
    )

    with st.expander("Auxiliary geometry (not intervallic homogeneity)", expanded=False):
        st.caption(
            "Span and compactness describe register layout; for registral dispersion use your dedicated tool. "
            "**Cluster compactness** is 1 − (avg pairwise distance / span); every **dyad** yields 0.0 here, "
            "so it is not an absolute density measure—use only as a rough spread ratio within larger sets."
        )
        st.write(f"Cluster compactness (custom): **{compactness_score:.3f}**")
        st.write(f"Pitch span (cents): **{pitch_span}**")
        st.write(f"Avg pairwise distance (cents): **{avg_distance:.3f}**")

    if intervallic_profile is not None:
        _render_intervallic_supplement(w, intervallic_profile, pc_set_summary)

    with st.expander("Pitch-class set detail (12-EDO)", expanded=False):
        if w.edo != 12:
            st.caption(
                "Prime form and Allen Forte interval vector use octave equivalence on twelve chromatic steps. "
                "Select **12-EDO** in Analysis mode to enable them."
            )
        elif pc_set_summary is None:
            st.info(
                "Set-class summary needs integer chromatic steps (no residual microtonal spellings such as "
                "quarter-tones in manual entry)."
            )
        else:
            st.caption(
                "**Normal order** is the most compact rotation of the pitch-class cycle. **Prime form** is the "
                "lexicographically smallest form among all transpositions and inversions (Forte convention). "
                "The **interval vector** counts unordered pairs by interval class 1–6 (semitones). "
                "These are orthogonal to the register-sensitive pairwise tables below."
            )
            st.write(f"**Pitch classes (sorted):** `{pc_set_summary['pitch_classes_sorted']}`")
            st.write(f"**Normal order:** {pc_set_summary['normal_order_str']}")
            st.write(f"**Prime form:** {pc_set_summary['prime_form_str']}")
            st.write(
                f"**Interval vector** (ic1–ic6): {pc_set_summary['interval_vector_str']} "
                f"(cardinality {pc_set_summary['cardinality']})"
            )

    if w.mode == AnalysisThresholdMode.FIXED_HEURISTIC:
        st.subheader("Why these numbers")
        if w.homogeneity_method == HomogeneityMethod.COMBINED:
            chain_dom = metrics["chain_dom"]
            pair_dom = metrics["pair_dom"]
            chain_ent = metrics["chain_ent"]
            pair_ent = metrics["pair_ent"]
            h_dom = metrics["H_dom"]
            h_ent = metrics["H_ent"]
            h_consensus = metrics["H_consensus"]
            alpha_line = (
                f"  (alpha_base = **{w.alpha_base:.2f}**, auto_adjust = **{w.auto_alpha}**, k = **{w.k_auto}**)\n"
                if w.intervallic_headline_mode == IntervallicHeadlineMode.HYBRID
                else f"  (Headline mode: **{w.intervallic_headline_mode.value}**; α not used.)\n"
            )
            st.write(
                f"- Chain dominance = **{chain_dom:.3f}**; Pairwise dominance = **{pair_dom:.3f}**.\n"
                f"- Chain concentration = **{chain_ent:.3f}**; Pairwise concentration = **{pair_ent:.3f}**.\n"
                f"- H_dominance = **{h_dom:.3f}**; H_entropy = **{h_ent:.3f}** (each uses the selected headline mode).\n"
                f"- H_consensus = **{h_consensus:.3f}** (geometric mean of the two).\n"
                f"{alpha_line}"
                f"- Evenness (pairwise absolute distances, span-normalized) = **{evenness_score:.3f}**."
            )
        else:
            chain_score = metrics["chain_score"]
            pair_score = metrics["pair_score"]
            ct = metrics.get("chain_metric_title", f"Chain {w.score_label}")
            pt = metrics.get("pair_metric_title", f"Pairwise {w.score_label}")
            et = metrics.get("evenness_title", "Evenness (entropy, pairwise)")
            if w.intervallic_headline_mode == IntervallicHeadlineMode.HYBRID:
                h_formula = (
                    f"- {metrics.get('H_primary_title', 'Homogeneity H')} = alpha_used·adjacent + (1−alpha_used)·pairwise "
                    f"with alpha_used = **{alpha_used:.3f}** → **{h_main:.3f}**.\n"
                    f"  (alpha_base = **{w.alpha_base:.2f}**, auto_adjust = **{w.auto_alpha}**, k = **{w.k_auto}**)\n"
                )
            else:
                h_formula = (
                    f"- {metrics.get('H_primary_title', 'Homogeneity H')} = **{h_main:.3f}** "
                    f"({w.intervallic_headline_mode.value}).\n"
                    f"  (Other constructions remain diagnostic in the metric suite.)\n"
                )
            st.write(
                f"- {ct} = **{chain_score:.3f}** (adjacent intervals after sorting pitches).\n"
                f"- {pt} = **{pair_score:.3f}** (all unordered pitch pairs).\n"
                f"{h_formula}"
                f"- {et} = **{evenness_score:.3f}**."
            )

    semi_rows = semi_distance_rows(distance_counts, total_intervals, bin_cents)
    st.subheader("Interval counts (pairwise, pitch-distance)")
    st.dataframe(semi_rows, width="stretch")

    st.subheader("Interval counts (adjacent/chain, pitch-distance)")
    adj_rows = adjacency_rows(adj_counts, note_count, bin_cents)
    st.dataframe(adj_rows, width="stretch")

    st.subheader("Interval counts (pairwise, labels)")
    interval_rows = interval_label_rows(interval_counts, total_intervals)
    st.dataframe(interval_rows, width="stretch")

    render_visualization_section(
        interval_rows=interval_rows,
        semi_rows=semi_rows,
        adj_rows=adj_rows,
        notes=notes,
        bin_cents=bin_cents,
        edo=w.edo,
        pc_set_summary=pc_set_summary,
    )

    st.subheader("Export")
    csv_text = analysis_csv_string(
        w,
        note_count,
        total_intervals,
        metrics,
        alpha_used,
        float(h_main),
        semi_rows,
        adj_rows,
        interval_rows,
        pc_set_summary,
    )

    st.download_button(
        "Download analysis CSV",
        data=csv_text,
        file_name="interval_analysis.csv",
        mime="text/csv",
    )

    input_name = ""
    if w.uploaded is not None:
        input_name = str(getattr(w.uploaded, "name", "") or "")
    analysis_mode = w.xml_mode if w.uploaded is not None else "manual"
    vc_profile = build_vertical_cardinality_profile(
        input_file=input_name,
        analysis_mode=analysis_mode,
        deduplication_active=deduplication_active,
        edo=w.edo,
        bin_cents=w.bin_cents,
        aggregate_notes=notes,
    )
    st.download_button(
        "Download vertical cardinality profile (JSON)",
        data=vertical_cardinality_profile_json(vc_profile),
        file_name="vertical_cardinality_profile.json",
        mime="application/json",
    )
