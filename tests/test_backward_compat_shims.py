"""Ensure legacy top-level module names still resolve to the packaged implementations."""

from __future__ import annotations

import analysis_core as ac_shim
import iav.interval_analysis_core as iac
import iav.musicxml_io as mx
import iav.pitch_model as pm
import interval_analysis as ia_shim
import pitch_model as pm_shim


def test_pitch_model_shim_aliases_package():
    assert pm_shim.chromatic_midi_float is pm.chromatic_midi_float
    assert pm_shim.spelled_note_from_chromatic_midi is pm.spelled_note_from_chromatic_midi


def test_analysis_core_shim_aliases_musicxml_io():
    assert ac_shim.parse_musicxml_bytes is mx.parse_musicxml_bytes
    assert ac_shim.get_musicxml_bytes is mx.get_musicxml_bytes


def test_interval_analysis_shim_aliases_core():
    assert ia_shim.metrics_for_notes is iac.metrics_for_notes
    assert ia_shim.homogeneity_score is iac.homogeneity_score
    assert ia_shim.chromatic_midi_float is pm.chromatic_midi_float
