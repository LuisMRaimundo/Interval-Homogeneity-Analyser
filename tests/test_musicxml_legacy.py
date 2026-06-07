"""Characterization tests for Streamlit-facing ``iav.musicxml`` (no production edits)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest
from defusedxml import ElementTree as ET

from iav.analysis_enums import (
    AnalysisThresholdMode,
    HomogeneityMethod,
    HomogeneityScoreKind,
    IntervallicHeadlineMode,
    MusicXmlImportMode,
    VerticalitySliceMode,
)
from iav.constants import FORCE_DEDUPE_THRESHOLD
from iav.musicxml import apply_dedupe_policy, ingest_musicxml
from iav.musicxml_io import parse_musicxml_upload
from iav.widget_state import WidgetState

ROOT = Path(__file__).resolve().parent.parent
MAJOR_TRIAD = ROOT / "validation" / "canonical" / "major_triad.xml"
MULTI_VOICE = ROOT / "validation" / "corpus" / "multi_voice_same_measure.xml"


class _FakeUpload:
    def __init__(self, data: bytes, name: str = "test.xml") -> None:
        self._data = data
        self.name = name

    def getvalue(self) -> bytes:
        return self._data


class _StreamlitStop(Exception):
    """Raised when stubbed ``st.stop`` is invoked."""


def _widget_state(**overrides: Any) -> WidgetState:
    defaults: Dict[str, Any] = {
        "data": [],
        "uploaded": None,
        "xml_mode": MusicXmlImportMode.AGGREGATE,
        "min_slice_notes": 2,
        "include_grace_notes": False,
        "include_cue_notes": False,
        "slice_mode": VerticalitySliceMode.SINGLE,
        "remove_duplicates": False,
        "edo": 12,
        "bin_cents": 100,
        "mode": AnalysisThresholdMode.STANDARD,
        "dominance_threshold": 0.35,
        "even_high": 0.8,
        "even_low": 0.3,
        "chain_threshold": 0.60,
        "homogeneity_method": HomogeneityMethod.DOMINANCE,
        "score_label": HomogeneityScoreKind.DOMINANCE,
        "intervallic_headline_mode": IntervallicHeadlineMode.PAIRWISE,
        "alpha_base": 0.6,
        "auto_alpha": False,
        "k_auto": 4,
        "merge_manual": False,
        "apply_sounding_transpose": False,
    }
    defaults.update(overrides)
    return WidgetState(**defaults)


@pytest.fixture
def stub_streamlit(monkeypatch: pytest.MonkeyPatch) -> Dict[str, List[str]]:
    calls: Dict[str, List[str]] = {"warnings": [], "errors": [], "captions": []}

    monkeypatch.setattr("iav.musicxml.st.warning", lambda msg: calls["warnings"].append(str(msg)))
    monkeypatch.setattr("iav.musicxml.st.error", lambda msg: calls["errors"].append(str(msg)))
    monkeypatch.setattr("iav.musicxml.st.caption", lambda msg: calls["captions"].append(str(msg)))
    monkeypatch.setattr("iav.musicxml.st.subheader", lambda *a, **k: None)
    monkeypatch.setattr("iav.musicxml.st.stop", lambda: (_ for _ in ()).throw(_StreamlitStop()))
    monkeypatch.setattr("iav.musicxml.st.data_editor", lambda df, **kwargs: df)
    monkeypatch.setattr(
        "iav.musicxml.st.selectbox",
        lambda label, options, format_func, index: options[index],
    )
    monkeypatch.setattr("iav.musicxml.st.altair_chart", lambda *a, **k: None)
    monkeypatch.setattr("iav.musicxml.st.dataframe", lambda *a, **k: None)
    monkeypatch.setattr("iav.musicxml.st.download_button", lambda *a, **k: None)
    monkeypatch.setattr("iav.musicxml.st.slider", lambda *a, **k: k.get("value", (0.0, 1.0)))
    monkeypatch.setattr("iav.musicxml.st.info", lambda *a, **k: None)
    return calls


def test_apply_dedupe_policy_no_upload_without_checkbox():
    w = _widget_state(remove_duplicates=False, uploaded=None)
    notes = [("C", 0.0, 4), ("C", 0.0, 4), ("E", 0.0, 4)]
    out, active = apply_dedupe_policy(w, notes)
    assert out == notes
    assert active is False


def test_apply_dedupe_policy_checkbox_collapses_duplicates():
    w = _widget_state(remove_duplicates=True, uploaded=None)
    notes = [("C", 0.0, 4), ("C", 0.0, 4), ("E", 0.0, 4)]
    out, active = apply_dedupe_policy(w, notes)
    assert len(out) == 2
    assert active is True


def test_apply_dedupe_policy_force_dedupe_large_upload(stub_streamlit, monkeypatch):
    warned: List[str] = []

    def _warn(msg: str) -> None:
        warned.append(str(msg))

    monkeypatch.setattr("iav.musicxml.st.warning", _warn)
    w = _widget_state(
        remove_duplicates=False,
        uploaded=_FakeUpload(b"<score-partwise/>"),
    )
    notes = [("C", 0.0, 4)] * FORCE_DEDUPE_THRESHOLD
    out, active = apply_dedupe_policy(w, notes)
    assert len(out) == 1
    assert active is True
    assert any("Large MusicXML upload" in m for m in warned)


def test_ingest_musicxml_no_upload_passthrough():
    w = _widget_state(uploaded=None)
    seed = [("G", 0.0, 3)]
    notes, skipped = ingest_musicxml(w, list(seed))
    assert notes == seed
    assert skipped == 0


def test_ingest_musicxml_aggregate_delegates_to_musicxml_io(stub_streamlit):
    w = _widget_state(uploaded=_FakeUpload(MAJOR_TRIAD.read_bytes()))
    notes, skipped = ingest_musicxml(w, [])
    assert skipped == 0
    assert len(notes) == 3
    letters = {n[0] for n in notes}
    assert letters == {"C", "E", "G"}
    assert all(isinstance(n, tuple) and len(n) == 3 for n in notes)


def test_ingest_musicxml_aggregate_empty_emits_warning(stub_streamlit, monkeypatch):
    monkeypatch.setattr(
        "iav.musicxml.parse_musicxml_upload",
        lambda *a, **k: ([], 0),
    )
    w = _widget_state(uploaded=_FakeUpload(b"<score-partwise/>"))
    notes, skipped = ingest_musicxml(w, [("D", 0.0, 4)])
    assert notes == [("D", 0.0, 4)]
    assert skipped == 0
    assert any("No pitched notes" in m for m in stub_streamlit["warnings"])


def test_ingest_musicxml_aggregate_accumulates_skipped_microtonal(stub_streamlit, monkeypatch):
    monkeypatch.setattr(
        "iav.musicxml.parse_musicxml_upload",
        lambda *a, **k: ([("C", 0.0, 4)], 3),
    )
    w = _widget_state(uploaded=_FakeUpload(b"<score-partwise/>"))
    _, skipped = ingest_musicxml(w, [])
    assert skipped == 3


def test_ingest_musicxml_onset_single_slice_selects_dict_notes(stub_streamlit):
    w = _widget_state(
        uploaded=_FakeUpload(MULTI_VOICE.read_bytes()),
        xml_mode=MusicXmlImportMode.ONSET_VERTICALITIES,
        slice_mode=VerticalitySliceMode.SINGLE,
        min_slice_notes=2,
        include_grace_notes=True,
        include_cue_notes=True,
    )
    notes, skipped = ingest_musicxml(w, [])
    assert skipped == 0
    assert len(notes) == 2
    assert {n[0] for n in notes} == {"C", "E"}


def test_ingest_musicxml_all_slices_summary_stops_before_return(stub_streamlit):
    w = _widget_state(
        uploaded=_FakeUpload(MULTI_VOICE.read_bytes()),
        xml_mode=MusicXmlImportMode.ONSET_VERTICALITIES,
        slice_mode=VerticalitySliceMode.ALL_SLICES,
        min_slice_notes=2,
        include_grace_notes=True,
        include_cue_notes=True,
    )
    with pytest.raises(_StreamlitStop):
        ingest_musicxml(w, [])


def test_ingest_musicxml_parse_error_surfaces_message(stub_streamlit, monkeypatch):
    def _raise_parse_error(*_a, **_k):
        raise ET.ParseError("bad xml")

    monkeypatch.setattr("iav.musicxml.parse_musicxml_upload", _raise_parse_error)
    w = _widget_state(uploaded=_FakeUpload(b"not-xml"))
    notes, skipped = ingest_musicxml(w, [("F", 0.0, 3)])
    assert notes == [("F", 0.0, 3)]
    assert skipped == 0
    assert stub_streamlit["errors"] == ["Unable to parse the MusicXML file."]


def test_ingest_musicxml_value_error_surfaces_message(stub_streamlit, monkeypatch):
    monkeypatch.setattr(
        "iav.musicxml.parse_musicxml_upload",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("unsupported container")),
    )
    w = _widget_state(uploaded=_FakeUpload(b"<score-partwise/>"))
    notes, skipped = ingest_musicxml(w, [])
    assert notes == []
    assert skipped == 0
    assert stub_streamlit["errors"] == ["unsupported container"]


def test_parse_result_shapes_expected_by_ingest_musicxml():
    """AGGREGATE mode yields note tuples; verticality modes yield slice dicts."""
    data = MAJOR_TRIAD.read_bytes()
    aggregate_notes, _ = parse_musicxml_upload(
        data,
        MusicXmlImportMode.AGGREGATE,
        include_grace=False,
        include_cue=False,
        apply_sounding_transpose=False,
    )
    onset_slices, _ = parse_musicxml_upload(
        data,
        MusicXmlImportMode.ONSET_VERTICALITIES,
        include_grace=True,
        include_cue=True,
        apply_sounding_transpose=False,
    )
    assert isinstance(aggregate_notes[0], tuple)
    assert isinstance(onset_slices[0], dict)
    assert "time" in onset_slices[0]
    assert "notes" in onset_slices[0]
    assert isinstance(onset_slices[0]["notes"][0], tuple)
