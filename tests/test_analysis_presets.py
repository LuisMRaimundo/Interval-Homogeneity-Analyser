"""Tests for fixed analysis preset session values."""

from iav.analysis_enums import (
    AnalysisThresholdMode,
    IntervallicHeadlineMode,
    MusicXmlImportMode,
    VerticalitySliceMode,
)
from iav.analysis_presets import (
    KEY_ALPHA_BASE,
    KEY_AUTO_ALPHA,
    KEY_EDO,
    KEY_HEADLINE_METRIC,
    KEY_HOMOGENEITY_SCORING,
    KEY_INCLUDE_GRACE,
    KEY_MIN_SLICE_NOTES,
    KEY_SLICE_MODE,
    KEY_THRESHOLD_MODE,
    KEY_XML_MODE,
    AnalysisPresetId,
    ensure_widget_defaults,
    preset_session_values,
)


def test_ensure_widget_defaults_only_fills_missing_keys():
    session: dict = {KEY_MIN_SLICE_NOTES: 5}
    ensure_widget_defaults(session)
    assert session[KEY_MIN_SLICE_NOTES] == 5
    assert session[KEY_EDO] == 12


def test_manual_preset_shared_metrics():
    v = preset_session_values(AnalysisPresetId.MANUAL_SINGLE_CHORD)
    assert v[KEY_THRESHOLD_MODE] == AnalysisThresholdMode.FIXED_HEURISTIC.value
    assert v[KEY_HOMOGENEITY_SCORING] == "Dominance (max share)"
    assert v[KEY_HEADLINE_METRIC] == IntervallicHeadlineMode.PAIRWISE
    assert v[KEY_ALPHA_BASE] == 0.55
    assert v[KEY_AUTO_ALPHA] is False
    assert v[KEY_XML_MODE] == MusicXmlImportMode.AGGREGATE.value
    assert v[KEY_SLICE_MODE] == VerticalitySliceMode.SINGLE.value


def test_musicxml_onset_preset():
    v = preset_session_values(AnalysisPresetId.MUSICXML_SINGLE_CHORD_ONSET)
    assert v[KEY_XML_MODE] == MusicXmlImportMode.ONSET_VERTICALITIES.value
    assert v[KEY_SLICE_MODE] == VerticalitySliceMode.SINGLE.value
    assert v[KEY_INCLUDE_GRACE] is False


def test_musicxml_sounding_preset():
    v = preset_session_values(AnalysisPresetId.MUSICXML_SINGLE_CHORD_SOUNDING)
    assert v[KEY_XML_MODE] == MusicXmlImportMode.SOUNDING_VERTICALITIES.value


def test_musicxml_active_fragment_preset():
    v = preset_session_values(AnalysisPresetId.MUSICXML_ACTIVE_FRAGMENT)
    assert v[KEY_XML_MODE] == MusicXmlImportMode.ONSET_VERTICALITIES.value
    assert v[KEY_SLICE_MODE] == VerticalitySliceMode.TIME_WINDOW.value
    assert v[KEY_MIN_SLICE_NOTES] == 3
    assert v[KEY_HEADLINE_METRIC] == IntervallicHeadlineMode.PAIRWISE
