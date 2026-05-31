"""Preset resolution helpers (re-exports pure preset logic for UI layers)."""

from __future__ import annotations

from iav.analysis_presets import (
    KEY_PRESET_CHOICE,
    PRESET_DESCRIPTIONS,
    PRESET_LABELS,
    AnalysisPresetId,
    apply_preset_to_session,
    ensure_widget_defaults,
    preset_session_values,
)

__all__ = [
    "KEY_PRESET_CHOICE",
    "PRESET_DESCRIPTIONS",
    "PRESET_LABELS",
    "AnalysisPresetId",
    "apply_preset_to_session",
    "ensure_widget_defaults",
    "preset_session_values",
]


def preset_id_from_session_value(value: str) -> AnalysisPresetId:
    return AnalysisPresetId(value)
