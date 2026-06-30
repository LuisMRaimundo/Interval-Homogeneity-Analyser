"""Streamlit page: when to use each intervallic headline metric."""

from __future__ import annotations

import streamlit as st

from iav.metric_guide_content import METRIC_GUIDE_SECTIONS

st.set_page_config(page_title="Which metric to use?", layout="wide")
st.title("Which intervallic metric should I use?")
st.caption("Guide to headline **H** and the intervallic metric suite (symbolic analysis, not listening).")

st.info(METRIC_GUIDE_SECTIONS[0]["body"])

for section in METRIC_GUIDE_SECTIONS[1:]:
    if "when" in section:
        st.subheader(section["title"])
        st.markdown(f"**When:** {section['when']}")
        st.markdown(f"**Example:** {section['example']}")
        st.markdown(f"**Caveat:** {section['caveat']}")
    else:
        st.subheader(section["title"])
        st.markdown(section["body"])

st.divider()
st.markdown(
    """
### Quick decision table

| Your question | Headline metric |
|---------------|-----------------|
| How concentrated are **all** intervals in the sonority? | **Pairwise intervallic concentration** |
| Is the sonority built from **repeating adjacent** steps? | **Adjacent intervallic regularity** |
| Local pattern matters but **distant pairs** should still count (weakly)? | **Proximity-weighted** (linear or quadratic) |
| You want one number blending local + global (report **α**) | **Hybrid** |

For a **fixed comparable setup** (thesis, many examples), use **Analysis presets** on the main page and [ANALYSIS_PRESET.md](../ANALYSIS_PRESET.md) (pairwise headline **H** by default).

Return to **Interval_Homogeneity** via the sidebar to run an analysis.
"""
)
