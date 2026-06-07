#!/usr/bin/env python3
"""Generate deterministic JSON fixtures for interval homogeneity regression (phase 1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "corpus" / "fixtures" / "interval_homogeneity_regression"

NoteTuple = Tuple[str, float, int]

DEFAULT_ANALYSIS: Dict[str, Any] = {
    "homogeneity_method": "dominance",
    "bin_cents": 100,
    "hybrid_alpha": 0.6,
    "dominance_threshold": 0.35,
    "even_high": 0.8,
    "even_low": 0.3,
    "chain_threshold": 0.60,
    "intervallic_headline_mode": "pairwise_intervallic_concentration",
}

FIXTURES: Dict[str, Dict[str, Any]] = {
    "unison_dyad": {
        "description": "Degenerate dyad: duplicate C4. Two vertical events, one unique pitch height.",
        "tags": ["dyad", "degenerate", "duplicate"],
        "notes": [("C", 0.0, 4), ("C", 0.0, 4)],
        "qualitative": {
            "vertical_note_count": 2,
            "unique_pitch_heights": 1,
            "single_interval_concentration": True,
            "not_perceptual_consonance": True,
        },
    },
    "single_interval_dyad_perfect_fifth": {
        "description": "Dyad C4–G4: one pairwise interval type (P5 on 12-TET grid).",
        "tags": ["dyad", "single_interval"],
        "notes": [("C", 0.0, 4), ("G", 0.0, 4)],
        "qualitative": {"single_interval_concentration": True, "not_perceptual_consonance": True},
    },
    "minor_second_dyad": {
        "description": "Dyad C4–C#4: single m2 interval; high concentration does not imply consonance.",
        "tags": ["dyad", "single_interval", "dissonant_spelling"],
        "notes": [("C", 0.0, 4), ("C", 1.0, 4)],
        "qualitative": {"single_interval_concentration": True, "not_perceptual_consonance": True},
    },
    "chromatic_cluster_four": {
        "description": "Four consecutive semitones C4–D#4: regular adjacent spacing, diverse pairwise set.",
        "tags": ["cluster", "adjacent_vs_pairwise"],
        "notes": [("C", 0.0, 4), ("C", 1.0, 4), ("D", 0.0, 4), ("D", 1.0, 4)],
        "qualitative": {"chain_gt_pair": True},
    },
    "whole_tone_segment_four": {
        "description": "Whole-tone segment C4–F#4: uniform adjacent M2, broader pairwise distances.",
        "tags": ["whole_tone", "adjacent_vs_pairwise"],
        "notes": [("C", 0.0, 4), ("D", 0.0, 4), ("E", 0.0, 4), ("F", 1.0, 4)],
        "qualitative": {"chain_gt_pair": True},
    },
    "stacked_fourths": {
        "description": "Quartal stack C4–Eb5: repeated P4 adjacent intervals.",
        "tags": ["quartal", "regular_adjacent"],
        "notes": [("C", 0.0, 4), ("F", 0.0, 4), ("B", -1.0, 4), ("E", -1.0, 5)],
        "qualitative": {"chain_gt_pair": True},
    },
    "stacked_fifths": {
        "description": "Fifths stack C3–A4: repeated P5 adjacent intervals.",
        "tags": ["quintal", "regular_adjacent"],
        "notes": [("C", 0.0, 3), ("G", 0.0, 3), ("D", 0.0, 4), ("A", 0.0, 4)],
        "qualitative": {"chain_gt_pair": True},
    },
    "major_triad_close": {
        "description": "Closed major triad C4–E4–G4: three distinct pairwise interval types.",
        "tags": ["triad", "irregular_pairwise"],
        "notes": [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)],
        "qualitative": {"compare_with": "augmented_triad_symmetric"},
    },
    "augmented_triad_symmetric": {
        "description": "Augmented triad C4–E4–G#4: equal major-third division in 12-TET.",
        "tags": ["triad", "symmetric"],
        "notes": [("C", 0.0, 4), ("E", 0.0, 4), ("G", 1.0, 4)],
        "qualitative": {"stronger_than": "major_triad_close"},
    },
    "diminished_seventh_symmetric": {
        "description": "Diminished seventh C4–A4: symmetric minor-third tiling.",
        "tags": ["seventh", "symmetric"],
        "notes": [("C", 0.0, 4), ("E", -1.0, 4), ("G", -1.0, 4), ("A", 0.0, 4)],
        "qualitative": {"stronger_than": "dominant_seventh_irregular"},
    },
    "dominant_seventh_irregular": {
        "description": "Dominant seventh C4–Bb4: same cardinality as dim7, less regular pairwise profile.",
        "tags": ["seventh", "irregular"],
        "notes": [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4), ("B", -1.0, 4)],
        "qualitative": {"same_cardinality_as": "diminished_seventh_symmetric"},
    },
    "same_cardinality_different_distribution_A": {
        "description": "Four-note diatonic cluster C4–F4: compact scalar / adjacent regularity.",
        "tags": ["cardinality_control", "compact"],
        "notes": [("C", 0.0, 4), ("D", 0.0, 4), ("E", 0.0, 4), ("F", 0.0, 4)],
        "qualitative": {"cardinality": 4},
    },
    "same_cardinality_different_distribution_B": {
        "description": "Four-note wide/symmetric C4–C5: same cardinality, different interval distribution.",
        "tags": ["cardinality_control", "wide"],
        "notes": [("C", 0.0, 4), ("E", 0.0, 4), ("G", 1.0, 4), ("C", 0.0, 5)],
        "qualitative": {"cardinality": 4, "differs_from": "same_cardinality_different_distribution_A"},
    },
    "octave_duplication_case": {
        "description": "C4 C5 G4: octave duplication; model uses distinct pitch heights (no pc collapse).",
        "tags": ["octave", "register"],
        "notes": [("C", 0.0, 4), ("C", 0.0, 5), ("G", 0.0, 4)],
        "qualitative": {"octave_equivalence_applied": False},
    },
    "transposed_same_structure": {
        "description": "chromatic_cluster_four transposed up major second (D4–F#4).",
        "tags": ["metamorphic", "transposition"],
        "notes": [("D", 0.0, 4), ("D", 1.0, 4), ("E", 0.0, 4), ("E", 1.0, 4)],
        "reference_fixture": "chromatic_cluster_four",
        "qualitative": {"transposition_invariant": True},
    },
    "inversion_same_interval_multiset": {
        "description": "Inversion of major_triad_close around E4: E4 G#4 C#4.",
        "tags": ["metamorphic", "inversion"],
        "notes": [("E", 0.0, 4), ("G", 1.0, 4), ("C", 1.0, 4)],
        "reference_fixture": "major_triad_close",
        "qualitative": {"interval_multiset_preserved": True},
    },
    "EDO_24_microtonal_regular": {
        "description": "Quarter-tone chromatic segment on 24-EDO grid (bin_cents=50).",
        "tags": ["microtonal", "edo24"],
        "notes": [("C", 0.0, 4), ("C", 0.5, 4), ("D", 0.0, 4), ("D", 0.5, 4)],
        "analysis_override": {"bin_cents": 50, "edo": 24},
        "qualitative": {"regular_adjacent_spacing": True},
    },
    "EDO_bin_change_sensitivity": {
        "description": "Same four semitones analysed at bin_cents=100 vs 50 (modelling choice).",
        "tags": ["edo", "binning"],
        "notes": [("C", 0.0, 4), ("C", 1.0, 4), ("D", 0.0, 4), ("D", 1.0, 4)],
        "bin_variants": [100, 50],
        "qualitative": {"binning_is_modelling_choice": True},
    },
    "repeated_pitch_density_not_homogeneity": {
        "description": "C4 C4 C4 G4: duplicate pitches preserved in manual aggregate path.",
        "tags": ["duplicate", "density"],
        "notes": [("C", 0.0, 4), ("C", 0.0, 4), ("C", 0.0, 4), ("G", 0.0, 4)],
        "qualitative": {
            "duplicates_preserved_in_raw_metrics": True,
            "dedupe_collapses_to_dyad": True,
        },
    },
    "passage_changing_interval_field": {
        "description": "Three verticalities: chromatic cluster, whole-tone segment, diminished seventh.",
        "tags": ["passage", "multi_slice"],
        "slices": [
            {
                "slice_id": 1,
                "label": "chromatic_cluster",
                "notes": [("C", 0.0, 4), ("C", 1.0, 4), ("D", 0.0, 4), ("D", 1.0, 4)],
            },
            {
                "slice_id": 2,
                "label": "whole_tone_segment",
                "notes": [("C", 0.0, 4), ("D", 0.0, 4), ("E", 0.0, 4), ("F", 1.0, 4)],
            },
            {
                "slice_id": 3,
                "label": "diminished_seventh",
                "notes": [("C", 0.0, 4), ("E", -1.0, 4), ("G", -1.0, 4), ("A", 0.0, 4)],
            },
        ],
        "qualitative": {"changing_interval_profile": True},
    },
}


def _serialize_notes(notes: List[NoteTuple]) -> List[List[Any]]:
    return [[letter, alter, octave] for letter, alter, octave in notes]


def _fixture_payload(fixture_id: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema_version": 1,
        "fixture_id": fixture_id,
        "description": spec["description"],
        "tags": spec["tags"],
        "analysis": {**DEFAULT_ANALYSIS, **spec.get("analysis_override", {})},
        "qualitative": spec.get("qualitative", {}),
    }
    if "notes" in spec:
        payload["notes"] = _serialize_notes(spec["notes"])
    if "slices" in spec:
        payload["slices"] = [
            {
                "slice_id": s["slice_id"],
                "label": s["label"],
                "notes": _serialize_notes(s["notes"]),
            }
            for s in spec["slices"]
        ]
    if "reference_fixture" in spec:
        payload["reference_fixture"] = spec["reference_fixture"]
    if "bin_variants" in spec:
        payload["bin_variants"] = spec["bin_variants"]
    return payload


def main() -> int:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_ids: List[str] = []
    for fixture_id, spec in FIXTURES.items():
        path = FIXTURE_DIR / f"{fixture_id}.json"
        path.write_text(
            json.dumps(_fixture_payload(fixture_id, spec), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        manifest_ids.append(fixture_id)

    manifest = {
        "schema_version": 1,
        "suite": "interval_homogeneity_regression",
        "phase": 1,
        "fixture_count": len(manifest_ids),
        "fixtures": manifest_ids,
        "default_analysis": DEFAULT_ANALYSIS,
        "notes": (
            "Qualitative/metamorphic regression only. No locked scalar golden values in phase 1."
        ),
    }
    (FIXTURE_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(manifest_ids)} fixtures to {FIXTURE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
