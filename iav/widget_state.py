"""Shared Streamlit widget state for the analysis UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from iav.analysis_enums import (
    AnalysisThresholdMode,
    HomogeneityMethod,
    HomogeneityScoreKind,
    IntervallicHeadlineMode,
    MusicXmlImportMode,
    VerticalitySliceMode,
)


@dataclass(frozen=True)
class WidgetState:
    # st.data_editor may return a DataFrame; normalize with _coerce_manual_table_rows before analysis.
    data: Any
    uploaded: Optional[Any]
    xml_mode: MusicXmlImportMode
    min_slice_notes: int
    include_grace_notes: bool
    include_cue_notes: bool
    slice_mode: VerticalitySliceMode
    remove_duplicates: bool
    edo: int
    bin_cents: int
    mode: AnalysisThresholdMode
    dominance_threshold: float
    even_high: float
    even_low: float
    chain_threshold: float
    homogeneity_method: HomogeneityMethod
    score_label: HomogeneityScoreKind
    intervallic_headline_mode: IntervallicHeadlineMode
    alpha_base: float
    auto_alpha: bool
    k_auto: int
    merge_manual: bool
    apply_sounding_transpose: bool

    @property
    def blend_chain_in_h(self) -> bool:
        """Backward compatibility: hybrid headline mode."""
        return self.intervallic_headline_mode == IntervallicHeadlineMode.HYBRID
