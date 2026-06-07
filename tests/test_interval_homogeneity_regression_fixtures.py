"""
Qualitative and metamorphic invariants for interval homogeneity regression (phase 1).

No locked golden scalar values — structural and musicological-semantic checks only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pytest

from iav.analysis_enums import IntervallicHeadlineMode
from iav.canonical_corpus import analyze_sonority, notes_from_json_rows
from iav.interval_analysis_core import dedupe_notes_by_midi, metrics_for_notes
from iav.symbolic_profile import passage_delta_rows
from iav.vertical_cardinality import vertical_cardinality_for_notes

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "corpus" / "fixtures" / "interval_homogeneity_regression"
DOCS_PATH = ROOT / "docs" / "INTERVAL_HOMOGENEITY_REGRESSION_FIXTURES.md"

NoteTuple = Tuple[str, float, int]

SINGLE_NOTE_FIXTURES = {
    "unison_dyad",
    "single_interval_dyad_perfect_fifth",
    "minor_second_dyad",
}

PASSAGE_FIXTURE = "passage_changing_interval_field"

ALL_FIXTURE_IDS = [
    "unison_dyad",
    "single_interval_dyad_perfect_fifth",
    "minor_second_dyad",
    "chromatic_cluster_four",
    "whole_tone_segment_four",
    "stacked_fourths",
    "stacked_fifths",
    "major_triad_close",
    "augmented_triad_symmetric",
    "diminished_seventh_symmetric",
    "dominant_seventh_irregular",
    "same_cardinality_different_distribution_A",
    "same_cardinality_different_distribution_B",
    "octave_duplication_case",
    "transposed_same_structure",
    "inversion_same_interval_multiset",
    "EDO_24_microtonal_regular",
    "EDO_bin_change_sensitivity",
    "repeated_pitch_density_not_homogeneity",
    PASSAGE_FIXTURE,
]


def _fixture_path(fixture_id: str) -> Path:
    path = FIXTURE_DIR / f"{fixture_id}.json"
    if not path.exists():
        pytest.skip(
            f"fixture missing: {path.name} — run create_interval_homogeneity_regression_fixtures.py"
        )
    return path


def _load_fixture(fixture_id: str) -> Dict[str, Any]:
    return json.loads(_fixture_path(fixture_id).read_text(encoding="utf-8"))


def _analysis_params(payload: Dict[str, Any]) -> Dict[str, Any]:
    analysis = payload.get("analysis", {})
    return {
        "dominance_threshold": float(analysis.get("dominance_threshold", 0.35)),
        "even_high": float(analysis.get("even_high", 0.8)),
        "even_low": float(analysis.get("even_low", 0.3)),
        "hybrid_alpha": float(analysis.get("hybrid_alpha", 0.6)),
        "homogeneity_method": str(analysis.get("homogeneity_method", "dominance")),
        "bin_cents": int(analysis.get("bin_cents", 100)),
        "chain_threshold": float(analysis.get("chain_threshold", 0.60)),
    }


def _metrics(
    notes: Sequence[NoteTuple],
    params: Dict[str, Any],
) -> Dict[str, Any]:
    return metrics_for_notes(
        notes,
        params["dominance_threshold"],
        params["even_high"],
        params["even_low"],
        params["hybrid_alpha"],
        params["homogeneity_method"],
        bin_cents=params["bin_cents"],
        chain_threshold=params["chain_threshold"],
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )


def _notes_for_fixture(fixture_id: str) -> List[NoteTuple]:
    payload = _load_fixture(fixture_id)
    if "notes" in payload:
        return notes_from_json_rows(payload["notes"])
    if "slices" in payload:
        return notes_from_json_rows(payload["slices"][0]["notes"])
    raise KeyError(fixture_id)


def _analyze_fixture(fixture_id: str) -> Dict[str, Any]:
    payload = _load_fixture(fixture_id)
    params = _analysis_params(payload)
    if fixture_id == PASSAGE_FIXTURE:
        rows: List[Dict[str, Any]] = []
        for sl in payload["slices"]:
            notes = notes_from_json_rows(sl["notes"])
            m = _metrics(notes, params)
            rows.append(
                {
                    "slice_id": sl["slice_id"],
                    "label": sl["label"],
                    "metrics": m,
                    "analyzed": analyze_sonority(
                        notes,
                        hybrid_alpha=params["hybrid_alpha"],
                        homogeneity_method=params["homogeneity_method"],
                        bin_cents=params["bin_cents"],
                    ),
                }
            )
        return {"kind": "passage", "rows": rows, "params": params}
    notes = notes_from_json_rows(payload["notes"])
    return {
        "kind": "aggregate",
        "notes": notes,
        "params": params,
        "metrics": _metrics(notes, params),
        "analyzed": analyze_sonority(
            notes,
            hybrid_alpha=params["hybrid_alpha"],
            homogeneity_method=params["homogeneity_method"],
            bin_cents=params["bin_cents"],
        ),
    }


@pytest.mark.parametrize("fixture_id", ALL_FIXTURE_IDS)
def test_all_interval_regression_fixtures_parse_or_analyze(fixture_id: str):
    result = _analyze_fixture(fixture_id)
    if result["kind"] == "passage":
        assert len(result["rows"]) >= 2
        for row in result["rows"]:
            assert row["metrics"]["H"] is not None
    else:
        assert result["metrics"]["H"] is not None
        assert result["analyzed"]["pair_score"] is not None


def test_transposition_invariance():
    base_id = "chromatic_cluster_four"
    trans_id = "transposed_same_structure"
    base = _analyze_fixture(base_id)
    trans = _analyze_fixture(trans_id)
    tol = 1e-9
    for key in ("pair_score", "chain_score", "H"):
        assert base["metrics"][key] == pytest.approx(trans["metrics"][key], abs=tol)
    analyzed_keys = ("pair_score", "chain_score", "hybrid_score")
    for key in analyzed_keys:
        assert base["analyzed"][key] == pytest.approx(trans["analyzed"][key], abs=tol)


def test_dyad_concentration_not_consonance():
    """
    Perfect fifth and minor second dyads both show single-interval concentration.

    This does NOT validate acoustic or perceptual consonance — only interval-type
    concentration under the symbolic distance model.
    """
    fifth = _analyze_fixture("single_interval_dyad_perfect_fifth")
    minor = _analyze_fixture("minor_second_dyad")
    for label, result in (("fifth", fifth), ("minor_second", minor)):
        m = result["metrics"]
        assert m["pair_score"] == pytest.approx(1.0), label
        assert m["chain_score"] == pytest.approx(1.0), label
        assert m["H"] == pytest.approx(1.0), label
        assert len(m["distance_counts"]) <= 1, label


@pytest.mark.parametrize(
    "fixture_id",
    ["chromatic_cluster_four", "whole_tone_segment_four"],
)
def test_adjacent_vs_pairwise_distinction(fixture_id: str):
    result = _analyze_fixture(fixture_id)
    m = result["metrics"]
    assert m["chain_score"] > m["pair_score"]
    assert m["chain_score"] >= 0.95
    assert m["pair_score"] <= 0.55


def test_same_cardinality_different_distribution():
    a = _analyze_fixture("same_cardinality_different_distribution_A")
    b = _analyze_fixture("same_cardinality_different_distribution_B")
    assert len(a["notes"]) == len(b["notes"]) == 4
    assert a["metrics"]["distance_counts"] != b["metrics"]["distance_counts"]
    assert a["metrics"]["pair_score"] != pytest.approx(b["metrics"]["pair_score"])


def test_symmetric_chord_vs_irregular_chord():
    sym = _analyze_fixture("diminished_seventh_symmetric")
    irr = _analyze_fixture("dominant_seventh_irregular")
    assert len(sym["notes"]) == len(irr["notes"]) == 4
    assert sym["metrics"]["pair_score"] > irr["metrics"]["pair_score"]
    assert sym["metrics"]["chain_score"] > irr["metrics"]["chain_score"]

    aug = _analyze_fixture("augmented_triad_symmetric")
    maj = _analyze_fixture("major_triad_close")
    assert aug["metrics"]["pair_score"] > maj["metrics"]["pair_score"]


def test_repeated_pitch_policy():
    payload = _load_fixture("repeated_pitch_density_not_homogeneity")
    params = _analysis_params(payload)
    raw_notes = notes_from_json_rows(payload["notes"])
    deduped = dedupe_notes_by_midi(raw_notes, bin_cents=params["bin_cents"])

    raw_metrics = _metrics(raw_notes, params)
    dedup_metrics = _metrics(deduped, params)

    assert len(raw_notes) == 4
    assert len(deduped) == 2
    assert raw_metrics["pair_score"] != pytest.approx(dedup_metrics["pair_score"])
    assert dedup_metrics["pair_score"] == pytest.approx(1.0)
    assert raw_metrics["pair_score"] == pytest.approx(0.5)


def test_inversion_preserves_interval_multiset():
    base = _analyze_fixture("major_triad_close")
    inv = _analyze_fixture("inversion_same_interval_multiset")
    assert base["metrics"]["pair_score"] == pytest.approx(inv["metrics"]["pair_score"])
    assert sorted(base["metrics"]["distance_counts"].values()) == sorted(
        inv["metrics"]["distance_counts"].values()
    )
    assert sorted(base["metrics"]["distance_counts"].keys()) == sorted(
        inv["metrics"]["distance_counts"].keys()
    )


def test_edo_or_binning_sensitivity():
    micro = _analyze_fixture("EDO_24_microtonal_regular")
    assert micro["metrics"]["H"] is not None
    assert micro["metrics"]["distance_counts"]

    payload = _load_fixture("EDO_bin_change_sensitivity")
    notes = notes_from_json_rows(payload["notes"])
    params = _analysis_params(payload)
    m100 = _metrics(notes, params)
    m50 = _metrics(notes, {**params, "bin_cents": 50})
    assert m100["H"] != pytest.approx(m50["H"]) or m100["distance_counts"] != m50["distance_counts"]


def test_passage_interval_field_change():
    result = _analyze_fixture(PASSAGE_FIXTURE)
    rows = result["rows"]
    assert len(rows) == 3

    profiles = [row["metrics"]["distance_counts"] for row in rows]
    evenness = [row["metrics"]["evenness_score"] for row in rows]
    assert len({json.dumps(p, sort_keys=True) for p in profiles}) > 1
    assert len({round(e, 4) for e in evenness}) > 1

    summary_rows = [
        {"Slice": row["slice_id"], "H (interval dominance)": row["metrics"]["H"]}
        for row in rows
    ]
    with_delta = passage_delta_rows(summary_rows)
    assert len(with_delta) == 3
    assert "ΔH (prev slice)" in with_delta[0]
    assert any(r["ΔH (prev slice)"] is not None for r in with_delta[1:])


def test_unison_dyad_degenerate_case():
    payload = _load_fixture("unison_dyad")
    notes = notes_from_json_rows(payload["notes"])
    card = vertical_cardinality_for_notes(notes, bin_cents=100, edo=12)
    assert card["vertical_note_count"] == 2
    assert card["vertical_unique_pitch_count"] == 1
    m = _metrics(notes, _analysis_params(payload))
    assert m["pair_score"] == pytest.approx(1.0)


def test_octave_duplication_uses_distinct_heights():
    notes = _notes_for_fixture("octave_duplication_case")
    m = _metrics(notes, _analysis_params(_load_fixture("octave_duplication_case")))
    assert ("C", 0.0, 4) in notes and ("C", 0.0, 5) in notes
    assert len(m["distance_counts"]) > 1


def test_documentation_lists_all_fixtures():
    text = DOCS_PATH.read_text(encoding="utf-8")
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
    for fixture_id in manifest["fixtures"]:
        assert fixture_id in text, f"{fixture_id} missing from documentation"
    assert "not perceptual" in text.lower() or "not acoustic" in text.lower()
    assert "pairwise" in text.lower()
    assert "adjacent" in text.lower() or "chain" in text.lower()
