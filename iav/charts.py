"""Altair charts for interval and pitch visualizations (Streamlit-compatible)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import altair as alt
import pandas as pd

from iav.interval_analysis_core import format_note_display_label, note_to_units
from iav.symbolic_profile import _headline_h_column

NoteTuple = Tuple[str, float, int]


def chart_pairwise_by_label(interval_rows: List[dict]) -> alt.Chart:
    df = pd.DataFrame(interval_rows)
    if df.empty:
        return alt.Chart(df).mark_text(text="No data").properties(height=80)
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Interval:N", sort="-y", title="Interval (pitch-distance label)"),
            y=alt.Y("Count:Q", title="Pair count"),
            tooltip=["Interval", "Count", "Percent"],
        )
        .properties(title="Pairwise intervals (by label)", height=320)
    )


def chart_pairwise_by_cents(semi_rows: List[dict]) -> alt.Chart:
    df = pd.DataFrame(semi_rows)
    if df.empty:
        return alt.Chart(df).mark_text(text="No data").properties(height=80)
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Cents:Q", title="Interval size (cents)"),
            y=alt.Y("Count:Q", title="Pair count"),
            tooltip=["Cents", "Label", "Count", "Percent"],
        )
        .properties(title="Pairwise intervals (by cents)", height=320)
    )


def chart_adjacent_chain(adj_rows: List[dict]) -> alt.Chart:
    df = pd.DataFrame(adj_rows)
    if df.empty:
        return alt.Chart(df).mark_text(text="No data").properties(height=80)
    return (
        alt.Chart(df)
        .mark_bar(color="#2ca02c")
        .encode(
            x=alt.X("Cents:Q", title="Interval size (cents)"),
            y=alt.Y("Count:Q", title="Count (adjacent in sorted order)"),
            tooltip=["Cents", "Label", "Count", "Percent"],
        )
        .properties(title="Adjacent / chain intervals (sorted pitch order)", height=320)
    )


def chart_pitch_register(notes: Sequence[NoteTuple], bin_cents: int) -> alt.Chart:
    """Sorted pitches: index vs height in cents from lowest note."""
    if len(notes) < 1:
        return (
            alt.Chart(pd.DataFrame({"x": [0], "y": [0]}))
            .mark_point()
            .properties(height=80, title="No notes")
        )

    units = [note_to_units(*n, bin_cents=bin_cents) for n in notes]
    order = sorted(range(len(units)), key=lambda i: units[i])
    sorted_units = [units[i] for i in order]
    sorted_notes = [notes[i] for i in order]
    base = min(sorted_units)
    cents_from_low = [(u - base) * bin_cents for u in sorted_units]
    labels = [format_note_display_label(n[0], n[1], n[2]) for n in sorted_notes]
    df = pd.DataFrame(
        {
            "Voice order (low → high)": range(1, len(notes) + 1),
            "Height above bass (cents)": cents_from_low,
            "Pitch label": labels,
        }
    )
    points = (
        alt.Chart(df)
        .mark_circle(size=120, color="#d62728")
        .encode(
            x=alt.X("Voice order (low → high):Q", title="Sorted pitch index (1 = lowest)"),
            y=alt.Y("Height above bass (cents):Q", title="Register (cents above lowest note)"),
            tooltip=[
                alt.Tooltip("Pitch label:N", title="Display spelling"),
                alt.Tooltip("Voice order (low → high):Q", title="Sorted index (low → high)"),
                alt.Tooltip("Height above bass (cents):Q", title="Height (¢ above lowest)"),
            ],
        )
    )
    # Avoid overlapping labels; with few notes, show spellings on the chart
    if len(df) <= 24:
        text = (
            alt.Chart(df)
            .mark_text(align="left", baseline="bottom", dx=10, dy=-4, fontSize=11, color="#333333")
            .encode(
                x="Voice order (low → high):Q",
                y="Height above bass (cents):Q",
                text="Pitch label:N",
            )
        )
        chart = points + text
    else:
        chart = points
    return chart.properties(title="Pitch register (aggregate sonority)", height=280)


def chart_pitch_class_presence(pitch_classes_sorted: Sequence[int]) -> alt.Chart:
    """Bar per pitch class 0–11 (12-TET)."""
    present = set(int(p) % 12 for p in pitch_classes_sorted)
    df = pd.DataFrame(
        {
            "Pitch class": [f"{i} ({_pc_letter(i)})" for i in range(12)],
            "Present": [1 if i in present else 0 for i in range(12)],
        }
    )
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Pitch class:N", sort=None, title="Pitch class"),
            y=alt.Y("Present:Q", title="Present (1 = yes)", scale=alt.Scale(domain=[0, 1])),
            tooltip=["Pitch class", "Present"],
        )
        .properties(title="Pitch-class presence (12-TET, octave collapsed)", height=260)
    )


def _pc_letter(pc: int) -> str:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return names[pc % 12]


def parse_slice_time_quarters(time_value: Any) -> float:
    """Numeric score time from ``Time (quarters)`` or a label like ``1.250`` / ``1.0-2.5``."""
    if isinstance(time_value, (int, float)):
        return float(time_value)
    text = str(time_value).strip()
    if "-" in text:
        start_s, end_s = text.split("-", 1)
        return (float(start_s) + float(end_s)) / 2.0
    return float(text)


def homogeneity_timeline_dataframe(summary_rows: List[dict]) -> pd.DataFrame:
    """One row per slice for timeline charts (H vs score time)."""
    if not summary_rows:
        return pd.DataFrame()
    h_key = _headline_h_column(summary_rows[0])
    if h_key is None:
        return pd.DataFrame()
    records: List[Dict[str, Any]] = []
    for row in summary_rows:
        t_raw = row.get("Time (quarters)", row.get("Time"))
        try:
            t = parse_slice_time_quarters(t_raw)
            h = float(row[h_key])
        except (TypeError, ValueError):
            continue
        records.append(
            {
                "Slice": row.get("Slice"),
                "Time (quarters)": t,
                "Time label": row.get("Time", f"{t:.3f}"),
                "H": h,
                "Notes": row.get("Notes"),
                "H label": row.get("H label", ""),
            }
        )
    return pd.DataFrame(records)


def vertical_cardinality_timeline_dataframe(summary_rows: List[dict]) -> pd.DataFrame:
    """One row per slice for vertical symbolic thickness (note count over score time)."""
    if not summary_rows:
        return pd.DataFrame()
    records: List[Dict[str, Any]] = []
    for row in summary_rows:
        t_raw = row.get("Time (quarters)", row.get("Time"))
        try:
            t = parse_slice_time_quarters(t_raw)
        except (TypeError, ValueError):
            continue
        notes_raw = row.get("Notes")
        if notes_raw is None or notes_raw == "":
            continue
        try:
            n_notes = int(notes_raw)
        except (TypeError, ValueError):
            continue
        records.append(
            {
                "Slice": row.get("Slice"),
                "Time (quarters)": t,
                "Time label": row.get("Time", f"{t:.3f}"),
                "vertical_note_count": n_notes,
                "Unique pitches": row.get("Unique pitches"),
                "PC cardinality": row.get("PC cardinality"),
            }
        )
    return pd.DataFrame(records)


def chart_vertical_cardinality_over_time(summary_rows: List[dict]) -> alt.Chart:
    """Line chart of vertical note count (symbolic thickness) across verticality slices."""
    df = vertical_cardinality_timeline_dataframe(summary_rows)
    if df.empty:
        return (
            alt.Chart(pd.DataFrame({"msg": ["No timeline data"]}))
            .mark_text(text="No timeline data")
            .properties(height=80)
        )
    df = df.sort_values("Time (quarters)")
    title = (
        "Vertical Cardinality Profile over Time"
        if "Unique pitches" in df.columns and df["Unique pitches"].notna().any()
        else "Vertical Note Count over Time"
    )
    enc = {
        "x": alt.X("Time (quarters):Q", title="Time (quarters)"),
        "y": alt.Y(
            "vertical_note_count:Q",
            title="Number of vertical notes",
        ),
        "tooltip": [
            alt.Tooltip("Slice:O", title="Slice #"),
            alt.Tooltip("Time label:N", title="Time"),
            alt.Tooltip("Time (quarters):Q", format=".3f"),
            alt.Tooltip("vertical_note_count:Q", title="Vertical note count"),
            alt.Tooltip("Unique pitches:Q", title="Unique pitches"),
            alt.Tooltip("PC cardinality:Q", title="Pitch-class cardinality"),
        ],
    }
    line = alt.Chart(df).mark_line(color="#ff7f0e", interpolate="monotone").encode(**enc)
    points = alt.Chart(df).mark_circle(size=70, color="#ff7f0e").encode(**enc)
    return (line + points).properties(title=title, height=320)


def chart_homogeneity_over_time(summary_rows: List[dict]) -> alt.Chart:
    """Line chart of headline intervallic homogeneity across verticality slices."""
    df = homogeneity_timeline_dataframe(summary_rows)
    if df.empty:
        return (
            alt.Chart(pd.DataFrame({"msg": ["No timeline data"]}))
            .mark_text(text="No timeline data")
            .properties(height=80)
        )
    if len(df) < 2:
        return (
            alt.Chart(df)
            .mark_text(text="Need at least 2 slices for a timeline")
            .properties(height=80)
        )
    df = df.sort_values("Time (quarters)")
    y_title = "Intervallic homogeneity (H)"
    enc = {
        "x": alt.X("Time (quarters):Q", title="Score time (quarter-note units)"),
        "y": alt.Y("H:Q", title=y_title, scale=alt.Scale(domain=[0, 1])),
        "tooltip": [
            alt.Tooltip("Slice:O", title="Slice #"),
            alt.Tooltip("Time label:N", title="Time"),
            alt.Tooltip("Time (quarters):Q", format=".3f"),
            alt.Tooltip("H:Q", format=".3f", title="H"),
            alt.Tooltip("Notes:Q", title="Notes"),
            alt.Tooltip("H label:N", title="H band"),
        ],
    }
    line = alt.Chart(df).mark_line(color="#1f77b4", interpolate="monotone").encode(**enc)
    points = alt.Chart(df).mark_circle(size=70, color="#1f77b4").encode(**enc)
    return (line + points).properties(
        title="Intervallic homogeneity across time",
        height=340,
    )


def chart_interval_vector_bars(iv: Sequence[int]) -> alt.Chart:
    """Allen Forte interval vector ⟨n1…n6⟩ as bars."""
    df = pd.DataFrame(
        {
            "Interval class": [f"ic{i + 1}" for i in range(6)],
            "Pairs": list(iv),
        }
    )
    return (
        alt.Chart(df)
        .mark_bar(color="#9467bd")
        .encode(
            x=alt.X(
                "Interval class:N", sort=None, title="Interval class (semitones between 1 and 6)"
            ),
            y=alt.Y("Pairs:Q", title="Unordered pair count"),
            tooltip=["Interval class", "Pairs"],
        )
        .properties(title="Interval vector (12-TET set)", height=260)
    )


def render_visualization_section(
    *,
    interval_rows: List[dict],
    semi_rows: List[dict],
    adj_rows: List[dict],
    notes: Sequence[NoteTuple],
    bin_cents: int,
    edo: int,
    pc_set_summary: Optional[Any],
) -> None:
    """Call from Streamlit results view; uses st.altair_chart."""
    import streamlit as st

    with st.expander("Visualizations (charts)", expanded=True):
        st.caption(
            "Same data as the tables above. "
            "Pairwise = all unordered pairs; adjacent = consecutive pitches after sorting by height."
        )

        c1, c2 = st.columns(2)
        with c1:
            st.altair_chart(chart_pairwise_by_label(interval_rows), width="stretch")
        with c2:
            st.altair_chart(chart_pairwise_by_cents(semi_rows), width="stretch")

        c3, c4 = st.columns(2)
        with c3:
            st.altair_chart(chart_adjacent_chain(adj_rows), width="stretch")
        with c4:
            st.altair_chart(chart_pitch_register(notes, bin_cents), width="stretch")

        if edo == 12 and pc_set_summary is not None:
            st.markdown("**12-TET pitch-class set**")
            iv = pc_set_summary.get("interval_vector")
            pcs = pc_set_summary.get("pitch_classes_sorted")
            if iv is not None and pcs is not None:
                c5, c6 = st.columns(2)
                with c5:
                    st.altair_chart(chart_pitch_class_presence(pcs), width="stretch")
                with c6:
                    st.altair_chart(chart_interval_vector_bars(iv), width="stretch")
