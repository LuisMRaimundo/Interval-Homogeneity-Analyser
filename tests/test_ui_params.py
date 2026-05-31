"""Pure UI parameter helpers (no Streamlit)."""

from __future__ import annotations

import pytest

from iav.analysis_enums import (
    AnalysisThresholdMode,
    HomogeneityMethod,
    HomogeneityScoreKind,
    IntervallicHeadlineMode,
    MusicXmlImportMode,
    VerticalitySliceMode,
)
from iav.analysis_presets import AnalysisPresetId, KEY_HOMOGENEITY_SCORING, preset_session_values
from iav.ui_params import (
    analysis_bundle_from_session,
    bin_cents_for_edo,
    homogeneity_method_from_ui_label,
    score_kind_for_homogeneity_method,
    threshold_tuple_for_mode,
    validate_musicxml_slice_combo,
)
from iav.ui_result_formatting import headline_summary_line, interval_heterogeneity


def test_homogeneity_method_from_ui_label():
    assert homogeneity_method_from_ui_label("Dominance (max share)") == HomogeneityMethod.DOMINANCE
    assert homogeneity_method_from_ui_label("Entropy concentration (1 - entropy)") == (
        HomogeneityMethod.ENTROPY
    )
    assert homogeneity_method_from_ui_label("Combined view (both + consensus)") == (
        HomogeneityMethod.COMBINED
    )


def test_score_kind_mapping():
    assert score_kind_for_homogeneity_method(HomogeneityMethod.DOMINANCE) == HomogeneityScoreKind.DOMINANCE
    assert score_kind_for_homogeneity_method(HomogeneityMethod.ENTROPY) == HomogeneityScoreKind.CONCENTRATION
    assert score_kind_for_homogeneity_method(HomogeneityMethod.COMBINED) == HomogeneityScoreKind.CONSENSUS


def test_fixed_threshold_tuple():
    assert threshold_tuple_for_mode(AnalysisThresholdMode.FIXED_HEURISTIC) == (0.60, 0.80, 0.30, 0.60)


def test_bin_cents_edo():
    assert bin_cents_for_edo(12) == 100
    assert bin_cents_for_edo(24) == 50


def test_validate_musicxml_slice_combo():
    validate_musicxml_slice_combo(
        MusicXmlImportMode.ONSET_VERTICALITIES,
        VerticalitySliceMode.ALL_SLICES,
    )
    with pytest.raises(ValueError, match="Aggregate"):
        validate_musicxml_slice_combo(
            MusicXmlImportMode.AGGREGATE,
            VerticalitySliceMode.TIME_WINDOW,
        )


def test_analysis_bundle_from_session():
    session = dict(preset_session_values(AnalysisPresetId.MANUAL_SINGLE_CHORD))
    assert KEY_HOMOGENEITY_SCORING in session
    bundle = analysis_bundle_from_session(
        session,
        dominance_threshold=0.35,
        even_high=0.8,
        even_low=0.3,
        chain_threshold=0.6,
    )
    assert bundle.edo == 12
    assert bundle.homogeneity_method == HomogeneityMethod.DOMINANCE
    assert bundle.intervallic_headline_mode == IntervallicHeadlineMode.PAIRWISE


def test_interval_heterogeneity_formatting():
    assert interval_heterogeneity(0.75) == pytest.approx(0.25)
    line = headline_summary_line({"H": 0.8, "H_label": "homogeneous", "H_primary_title": "H"})
    assert "0.800" in line
    assert "homogeneous" in line
