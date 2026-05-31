"""MusicXML upload handling and verticality slice summaries."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from typing import Any, Dict, List, Optional, Tuple, cast

import pandas as pd
import streamlit as st
from defusedxml import ElementTree as ET

from iav.analysis_enums import HomogeneityMethod, MusicXmlImportMode, VerticalitySliceMode
from iav.constants import FORCE_DEDUPE_THRESHOLD, MAX_NOTES
from iav.interval_analysis_core import (
    compute_alpha_used,
    dedupe_notes_by_midi,
    format_note_display_label,
    format_note_spelling,
    metrics_for_notes,
    parse_manual_note_string,
    parse_note_name,
)
from iav.musicxml_io import parse_musicxml_upload
from iav.pitch_model import NOTE_BASE
from iav.charts import chart_homogeneity_over_time, chart_vertical_cardinality_over_time
from iav.symbolic_profile import passage_delta_rows, slice_intervallic_columns
from iav.vertical_cardinality import (
    build_vertical_cardinality_profile,
    enrich_slice_summary_row,
    vertical_cardinality_profile_json,
)
from iav.widgets import WidgetState

NoteList = List[Any]


def _slice_summary_dataframe(summary_rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """Arrow-safe table for st.dataframe (numeric ΔH column, no mixed str/float)."""
    df = pd.DataFrame(summary_rows)
    if "ΔH (prev slice)" in df.columns:
        df["ΔH (prev slice)"] = pd.to_numeric(df["ΔH (prev slice)"], errors="coerce")
    return df


def _pitch_rows_for_editor(xml_notes: NoteList) -> List[Dict[str, Any]]:
    """One Note column per pitch (e.g. C4, Eb5), same as manual entry."""
    return [
        {"Note": format_note_display_label(letter, alter, int(octave))}
        for letter, alter, octave in xml_notes
    ]


def _pitch_dataframe_for_editor(xml_notes: NoteList) -> pd.DataFrame:
    rows = _pitch_rows_for_editor(xml_notes)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["Note"] = df["Note"].fillna("C4").astype(str)
    return df


def _upload_bytes_fingerprint(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()[:16]


def _parse_note_cell(note_name: str) -> Optional[Tuple[str, float]]:
    """parse_note_name plus C(+0.50st)-style fallback from format_note_spelling."""
    note_name = note_name.strip()
    p = parse_note_name(note_name)
    if p is not None:
        return p
    m = re.match(r"^([A-Ga-g])\(([+-]?[0-9.]+)st\)$", note_name)
    if m:
        return m.group(1).upper(), float(m.group(2))
    return None


def _note_tuple_from_editor_row(row: Dict[str, Any]) -> Tuple[str, float, int]:
    note_name = str(row.get("Note", row.get("Nota", "C4"))).strip()
    try:
        default_oct = int(float(row.get("Octave", row.get("Oitava", 4))))
    except (TypeError, ValueError):
        default_oct = 4
    parsed = parse_manual_note_string(note_name, default_octave=default_oct)
    if parsed is not None:
        return parsed
    pc = _parse_note_cell(note_name)
    if pc is not None:
        letter, alter = pc
        if letter in NOTE_BASE:
            return letter, alter, default_oct
    st.error(f"Invalid note '{note_name}' (try C4, Eb5, F#3).")
    st.stop()


def _editor_output_to_note_tuples(data: Any) -> NoteList:
    if data is None:
        return []
    try:
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return []
            records = data.to_dict("records")
        else:
            records = list(data)
    except TypeError:
        records = list(data) if data else []
    return [_note_tuple_from_editor_row(cast(Dict[str, Any], r)) for r in records]


def _show_extracted_pitches_editable(
    xml_notes: NoteList,
    *,
    session_key_suffix: str,
    file_bytes: bytes,
) -> NoteList:
    """
    Show an editable table (letter, chromatic alter from natural, octave) and return the edited note list.
    """
    if not xml_notes:
        return []
    st.subheader("Pitches extracted from MusicXML")
    st.caption(
        "Same as **manual entry**: one **Note** per row (e.g. C4, C#, Eb5, C+4). "
        "Row order follows the file. Add or remove rows with +."
    )
    df_in = _pitch_dataframe_for_editor(xml_notes)
    # Stable key from file hash + suffix (aggregate vs slice) so Streamlit state resets cleanly on new uploads
    editor_key = f"xml_pitch_edit_{_upload_bytes_fingerprint(file_bytes)}_{session_key_suffix}"
    edited = st.data_editor(
        df_in,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "Note": st.column_config.TextColumn("Note", help="e.g. C4, Eb5, F#3, C+4"),
        },
        key=editor_key,
    )
    return _editor_output_to_note_tuples(edited)


def ingest_musicxml(w: WidgetState, notes: NoteList) -> Tuple[NoteList, int]:
    """
    Extend notes from uploaded MusicXML. Returns (notes, skipped_microtonal_total).
    May st.stop() after slice-summary download.
    """
    skipped_microtonal_total = 0
    uploaded = w.uploaded

    if uploaded is None:
        return notes, skipped_microtonal_total

    try:
        if w.xml_mode == MusicXmlImportMode.AGGREGATE:
            xml_notes, skipped_microtonal = parse_musicxml_upload(
                uploaded.getvalue(),
                w.xml_mode,
                include_grace=w.include_grace_notes,
                include_cue=w.include_cue_notes,
                apply_sounding_transpose=w.apply_sounding_transpose,
            )
            skipped_microtonal_total += skipped_microtonal
            if not xml_notes:
                st.warning("No pitched notes found in the MusicXML file.")
            else:
                if len(xml_notes) > 50:
                    st.warning(
                        "This MusicXML contains many notes. This app treats ALL pitched notes as one aggregate "
                        "(no time slicing). For chord-level aggregates, upload a file containing only the target sonority "
                        "or rely on 'Collapse to unique pitches'."
                    )
                xml_notes = _show_extracted_pitches_editable(
                    xml_notes,
                    session_key_suffix="agg",
                    file_bytes=uploaded.getvalue(),
                )
            notes.extend(xml_notes)
        else:
            slices, skipped_microtonal = parse_musicxml_upload(
                uploaded.getvalue(),
                w.xml_mode,
                include_grace=w.include_grace_notes,
                include_cue=w.include_cue_notes,
                apply_sounding_transpose=w.apply_sounding_transpose,
            )

            skipped_microtonal_total += skipped_microtonal
            if not slices:
                st.warning("No pitched notes found in the MusicXML file.")
            else:
                if w.xml_mode == MusicXmlImportMode.SOUNDING_VERTICALITIES:
                    filtered = [s for s in slices if len(s["notes"]) >= w.min_slice_notes]
                    slice_count = len(filtered)
                    st.caption(
                        f"Extracted {slice_count} slices (filtered from {len(slices)} total) by active set."
                    )
                else:
                    filtered = [s for s in slices if len(s["notes"]) >= w.min_slice_notes]
                    slice_count = len(filtered)
                    st.caption(
                        f"Extracted {slice_count} slices (filtered from {len(slices)} total) by onset time."
                    )

                if not filtered:
                    st.warning("No slices meet the minimum note count.")
                else:
                    if w.xml_mode == MusicXmlImportMode.SOUNDING_VERTICALITIES:
                        slice_labels = [
                            f"{idx + 1}: t={s['start']:.3f}-{s['end']:.3f} (n={len(s['notes'])})"
                            for idx, s in enumerate(filtered)
                        ]
                    else:
                        slice_labels = [
                            f"{idx + 1}: t={s['time']:.3f} (n={len(s['notes'])})"
                            for idx, s in enumerate(filtered)
                        ]

                    if w.slice_mode == VerticalitySliceMode.SINGLE:
                        slice_positions = list(range(len(filtered)))
                        selected_pos = st.selectbox(
                            "Choose slice to analyze",
                            options=slice_positions,
                            format_func=lambda i: slice_labels[i],
                            index=0,
                        )
                        selected_slice = filtered[selected_pos]
                        slice_notes = _show_extracted_pitches_editable(
                            selected_slice["notes"],
                            session_key_suffix=f"slice_{selected_pos}",
                            file_bytes=uploaded.getvalue(),
                        )
                        notes.extend(slice_notes)
                    else:
                        if w.xml_mode == MusicXmlImportMode.SOUNDING_VERTICALITIES:
                            min_t = min(s["start"] for s in filtered)
                            max_t = max(s["end"] for s in filtered)
                        else:
                            min_t = min(s["time"] for s in filtered)
                            max_t = max(s["time"] for s in filtered)

                        if w.slice_mode == VerticalitySliceMode.TIME_WINDOW:
                            min_f, max_f = float(min_t), float(max_t)
                            if max_f <= min_f:
                                st.caption(
                                    "Only one slice time in the filtered set "
                                    f"({min_f:.3f} quarter-note units); using that moment."
                                )
                                w_start, w_end = min_f, max_f
                            else:
                                window = st.slider(
                                    "Select time window (quarter units)",
                                    min_value=min_f,
                                    max_value=max_f,
                                    value=(min_f, max_f),
                                    step=0.01,
                                )
                                w_start, w_end = float(window[0]), float(window[1])
                            if w.xml_mode == MusicXmlImportMode.SOUNDING_VERTICALITIES:
                                scoped = [
                                    s for s in filtered if s["end"] > w_start and s["start"] < w_end
                                ]
                            else:
                                scoped = [s for s in filtered if w_start <= s["time"] <= w_end]
                        else:
                            scoped = filtered

                        if not scoped:
                            st.warning("No slices fall within the selected window.")
                        else:
                            summary_rows = []
                            skipped_too_few = 0
                            skipped_too_many = 0
                            for idx, s in enumerate(scoped, start=1):
                                slice_notes = s["notes"]
                                if w.remove_duplicates:
                                    slice_notes = dedupe_notes_by_midi(
                                        slice_notes, bin_cents=w.bin_cents
                                    )
                                if len(slice_notes) < 2:
                                    skipped_too_few += 1
                                    continue
                                if len(slice_notes) > MAX_NOTES:
                                    skipped_too_many += 1
                                    continue
                                alpha_used = compute_alpha_used(
                                    len(slice_notes), w.alpha_base, w.auto_alpha, w.k_auto
                                )
                                metrics = metrics_for_notes(
                                    slice_notes,
                                    w.dominance_threshold,
                                    w.even_high,
                                    w.even_low,
                                    alpha_used,
                                    w.homogeneity_method,
                                    bin_cents=w.bin_cents,
                                    chain_threshold=w.chain_threshold,
                                    intervallic_headline_mode=w.intervallic_headline_mode,
                                )
                                if w.xml_mode == MusicXmlImportMode.SOUNDING_VERTICALITIES:
                                    time_q = float(s["start"])
                                    label_time = f"{s['start']:.3f}-{s['end']:.3f}"
                                else:
                                    time_q = float(s["time"])
                                    label_time = f"{s['time']:.3f}"
                                sym_cols = slice_intervallic_columns(
                                    slice_notes, metrics.as_dict(), w.bin_cents
                                )
                                if w.homogeneity_method == HomogeneityMethod.COMBINED:
                                    row = {
                                        "Slice": idx,
                                        "Time": label_time,
                                        "Time (quarters)": time_q,
                                        "H (dominance)": round(metrics["H_dom"], 3),
                                        "H (entropy)": round(metrics["H_ent"], 3),
                                        "H (consensus)": round(metrics["H_consensus"], 3),
                                        "Pairwise dominance": round(metrics["pair_dom"], 3),
                                        "Chain dominance": round(metrics["chain_dom"], 3),
                                        "Pairwise concentration": round(metrics["pair_ent"], 3),
                                        "Chain concentration": round(metrics["chain_ent"], 3),
                                        "Interval evenness (span-norm.)": round(
                                            metrics["evenness_score"], 3
                                        ),
                                        "Label": metrics["classification"],
                                        "H label": metrics["H_label"],
                                    }
                                else:
                                    if w.homogeneity_method == HomogeneityMethod.ENTROPY:
                                        h_col = "H (interval entropy concentration)"
                                        pair_col = "Pairwise entropy concentration"
                                        chain_col = "Chain entropy concentration"
                                    else:
                                        h_col = "H (interval dominance)"
                                        pair_col = "Pairwise dominance"
                                        chain_col = "Chain dominance"
                                    row = {
                                        "Slice": idx,
                                        "Time": label_time,
                                        "Time (quarters)": time_q,
                                        h_col: round(metrics["H"], 3),
                                        pair_col: round(metrics["pair_score"], 3),
                                        chain_col: round(metrics["chain_score"], 3),
                                        "Interval evenness (span-norm.)": round(
                                            metrics["evenness_score"], 3
                                        ),
                                        "Label": metrics["classification"],
                                        "H label": metrics["H_label"],
                                    }
                                row.update(sym_cols)
                                enrich_slice_summary_row(
                                    row,
                                    slice_notes,
                                    bin_cents=w.bin_cents,
                                    edo=w.edo,
                                )
                                summary_rows.append(row)
                            if summary_rows:
                                summary_rows = passage_delta_rows(summary_rows)
                                st.subheader("Slice summary (intervallic homogeneity over time)")
                                st.caption(
                                    "**ΔH** compares headline intervallic homogeneity to the previous slice "
                                    "in table order (score time). Not registral dispersion."
                                )
                                st.altair_chart(
                                    chart_homogeneity_over_time(summary_rows),
                                    width="stretch",
                                )
                                st.altair_chart(
                                    chart_vertical_cardinality_over_time(summary_rows),
                                    width="stretch",
                                )
                                st.caption(
                                    "Vertical cardinality counts symbolic notes per slice "
                                    "(not acoustic density, loudness, or spectral mass)."
                                )
                                st.dataframe(_slice_summary_dataframe(summary_rows), width="stretch")
                                csv_buffer = io.StringIO()
                                writer = csv.DictWriter(
                                    csv_buffer, fieldnames=summary_rows[0].keys()
                                )
                                writer.writeheader()
                                for row in summary_rows:
                                    writer.writerow(
                                        {
                                            k: ("" if v is None else v)
                                            for k, v in row.items()
                                        }
                                    )
                                st.download_button(
                                    "Download slice summary CSV",
                                    data=csv_buffer.getvalue(),
                                    file_name="slice_summary.csv",
                                    mime="text/csv",
                                )
                                vc_profile = build_vertical_cardinality_profile(
                                    input_file=str(getattr(uploaded, "name", "") or ""),
                                    analysis_mode=w.xml_mode,
                                    deduplication_active=bool(w.remove_duplicates),
                                    edo=w.edo,
                                    bin_cents=w.bin_cents,
                                    summary_rows=summary_rows,
                                )
                                st.download_button(
                                    "Download vertical cardinality profile (JSON)",
                                    data=vertical_cardinality_profile_json(vc_profile),
                                    file_name="vertical_cardinality_profile.json",
                                    mime="application/json",
                                )
                                st.stop()
                            skipped_total = skipped_too_few + skipped_too_many
                            if skipped_total:
                                st.info(
                                    f"Skipped {skipped_total} slice(s) in this window: "
                                    f"{skipped_too_few} with fewer than 2 notes after dedupe, "
                                    f"{skipped_too_many} with more than {MAX_NOTES} notes."
                                )
                            st.error(
                                "No slices in this selection have 2–500 notes after filtering. "
                                "Lower **Minimum notes per slice**, widen **Select time window**, "
                                "or use **Single slice** for one chord."
                            )
                            st.stop()
    except ET.ParseError:
        st.error("Unable to parse the MusicXML file.")
    except ValueError as exc:
        st.error(str(exc))

    return notes, skipped_microtonal_total


def apply_dedupe_policy(
    w: WidgetState,
    notes: NoteList,
) -> Tuple[NoteList, bool]:
    """Collapse duplicates per checkbox or large-upload rule."""
    remove_duplicates = w.remove_duplicates
    if remove_duplicates:
        notes = dedupe_notes_by_midi(notes, bin_cents=w.bin_cents)
    elif w.uploaded is not None and len(notes) >= FORCE_DEDUPE_THRESHOLD:
        st.warning(
            "Large MusicXML upload detected. To avoid excessive computation, "
            "duplicates were collapsed to unique pitches."
        )
        notes = dedupe_notes_by_midi(notes, bin_cents=w.bin_cents)
        remove_duplicates = True
    return notes, remove_duplicates
