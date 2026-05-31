"""Streamlit entry: Interval Aggregate Analyzer."""

import streamlit as st

from interval_analyzer_ui import render_analysis


def ensure_streamlit_context():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except (ImportError, ModuleNotFoundError):
        return True
    if get_script_run_ctx() is None:
        print("This app must be run with: streamlit run app.py")
        return False
    return True


if not ensure_streamlit_context():
    raise SystemExit(0)

st.set_page_config(page_title="Interval Aggregate Analyzer", layout="wide")
st.sidebar.page_link("pages/1_Which_metric_to_use.py", label="Which metric to use?")
st.title("Interval Aggregate Analyzer")
st.write(
    "Enter notes manually or upload MusicXML. By default, headline **H** is "
    "**pairwise intervallic concentration** on the chosen tuning grid "
    "(how concentrated the unordered pitch-distance multiset is). "
    "Adjacent, proximity-weighted, and hybrid modes are optional; the metric suite always "
    "lists all constructions. This app does **not** analyse registral dispersion or listening."
)
render_analysis()
