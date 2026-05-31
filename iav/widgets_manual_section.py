"""Manual note table (Streamlit data editor + hints)."""



from __future__ import annotations



from typing import Any



import pandas as pd

import streamlit as st



from iav.interval_analysis_core import (

    format_note_display_label,

    manual_input_hints,

    parse_manual_note_string,

    parse_note_name,

)

from iav.widget_constants import ACCIDENTAL_CHOICES



_MANUAL_TABLE_KEY = "manual_notes_table"





def _default_manual_dataframe() -> pd.DataFrame:

    return pd.DataFrame([{"Note": ""}])





def _sanitize_manual_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    """Single Note column (e.g. C4, Eb5); migrate legacy Note + Octave tables."""

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:

        return _default_manual_dataframe()

    out = df.copy().reset_index(drop=True)

    n = len(out)

    raw_notes = out["Note"].astype(str) if "Note" in out.columns else pd.Series([""] * n, dtype=str)

    octaves = None

    if "Octave" in out.columns:

        octaves = pd.to_numeric(out["Octave"], errors="coerce").fillna(4).astype(int)



    merged: list[str] = []

    for i in range(n):

        text = str(raw_notes.iloc[i]).strip()

        if not text:

            merged.append("")

            continue

        if parse_manual_note_string(text) is not None:

            merged.append(text)

            continue

        default_oct = int(octaves.iloc[i]) if octaves is not None else 4

        parsed_pc = parse_note_name(text)

        if parsed_pc is not None:

            letter, alter = parsed_pc

            merged.append(format_note_display_label(letter, alter, default_oct))

        else:

            merged.append(text)

    return pd.DataFrame({"Note": merged})





def render_manual_section() -> Any:

    with st.expander("Manual input", expanded=True):

        st.caption(

            "One note per row, usual spelling: **C4**, **F#3**, **Bb5**, **C+4** (quarter-sharp). "

            "Pitch without a number defaults to octave **4**."

        )

        with st.expander("Accidental reference (#, b, and smaller steps)", expanded=False):

            idx = st.selectbox(

                "Accidental type (example uses middle register)",

                options=list(range(len(ACCIDENTAL_CHOICES))),

                format_func=lambda i: ACCIDENTAL_CHOICES[i][0],

                key="accidental_menu_pick",

            )

            _label, suffix = ACCIDENTAL_CHOICES[idx]

            example = f"C{suffix}4" if suffix else "C4"

            st.code(example, language=None)

            if suffix in ("+", "-", "1.5", "-1.5"):

                st.caption(

                    "Use tuning **24-EDO** or **48-EDO** so quarter-steps are not rounded away."

                )

        if _MANUAL_TABLE_KEY not in st.session_state:

            st.session_state[_MANUAL_TABLE_KEY] = _default_manual_dataframe()

        else:

            st.session_state[_MANUAL_TABLE_KEY] = _sanitize_manual_dataframe(

                st.session_state[_MANUAL_TABLE_KEY]

            )



        edited = st.data_editor(

            _sanitize_manual_dataframe(st.session_state[_MANUAL_TABLE_KEY]),

            num_rows="dynamic",

            width="stretch",

            hide_index=True,

            column_config={

                "Note": st.column_config.TextColumn(

                    "Note",

                    help="e.g. C4, Eb5, F##3, C+4",

                    default="",

                    width="large",

                ),

            },

            key="manual_notes_editor",

        )

        st.session_state[_MANUAL_TABLE_KEY] = _sanitize_manual_dataframe(edited)

        data = st.session_state[_MANUAL_TABLE_KEY]

        for _hint in manual_input_hints(data):

            st.warning(_hint)

    return data

