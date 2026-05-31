"""Preset ① defaults must yield pairwise headline H (not silent hybrid)."""

from __future__ import annotations

from iav.analysis_enums import AnalysisThresholdMode, IntervallicHeadlineMode
from iav.analysis_presets import (
    AnalysisPresetId,
    preset_session_values,
)
from iav.interval_analysis_core import dedupe_notes_by_midi, metrics_for_notes

# Same pitch content as canonical chromatic_cluster_semitone (C4–F4 cluster).
CHROMATIC_CLUSTER = [
    ("C", 0.0, 4),
    ("C", 1.0, 4),
    ("D", 0.0, 4),
    ("D", 1.0, 4),
    ("E", 0.0, 4),
    ("F", 0.0, 4),
]


def _metrics_under_preset(preset_id: AnalysisPresetId):
    p = preset_session_values(preset_id)
    notes = CHROMATIC_CLUSTER
    if p["iav_remove_duplicates"]:
        notes = dedupe_notes_by_midi(notes, bin_cents=100)
    return metrics_for_notes(
        notes,
        0.60,
        0.80,
        0.30,
        0.60,
        "dominance",
        bin_cents=100,
        intervallic_headline_mode=p["iav_headline_metric"],
    )


def test_manual_preset_chromatic_cluster_pairwise_headline_h():
    m = _metrics_under_preset(AnalysisPresetId.MANUAL_SINGLE_CHORD)
    assert m["H"] == m["pair_score"]
    assert abs(m["H"] - 1 / 3) < 0.02
    assert abs(m["chain_score"] - 1.0) < 0.02
    assert m["H"] < m["chain_score"]


def test_preset_uses_fixed_thresholds_and_pairwise_mode():
    p = preset_session_values(AnalysisPresetId.MANUAL_SINGLE_CHORD)
    assert p["iav_threshold_mode"] == AnalysisThresholdMode.FIXED_HEURISTIC.value
    assert p["iav_headline_metric"] == IntervallicHeadlineMode.PAIRWISE
    assert p["iav_apply_sounding_transpose"] is False
