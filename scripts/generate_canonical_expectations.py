#!/usr/bin/env python3
"""Regenerate iav/data/canonical_sonorities.json from current metrics (dominance, 12-EDO)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iav.analysis_enums import IntervallicHeadlineMode  # noqa: E402
from iav.canonical_corpus import _corpus_path, analyze_sonority  # noqa: E402
from iav.interval_analysis_core._homogeneity import resolve_headline_h  # noqa: E402

# Source definitions (edit here when adding sonorities)
_DEFINITIONS: dict = {
    "dyad_perfect_fifth": {
        "notes": [("C", 0.0, 4), ("G", 0.0, 4)],
        "tags": ["dyad"],
        "constraints": {"pair_score_min": 0.99, "chain_score_min": 0.99},
    },
    "unison_duplicates": {
        "notes": [("C", 0.0, 4), ("C", 0.0, 4), ("E", 0.0, 4)],
        "tags": ["duplicate"],
    },
    "chromatic_cluster_semitone": {
        "notes": [
            ("C", 0.0, 4),
            ("C", 1.0, 4),
            ("D", 0.0, 4),
            ("D", 1.0, 4),
            ("E", 0.0, 4),
            ("F", 0.0, 4),
        ],
        "tags": ["chromatic", "adjacent_max"],
        "constraints": {
            "chain_score_min": 0.95,
            "pair_score_max": 0.99,
            "chain_gt_pair": True,
        },
    },
    "whole_tone_scale": {
        "notes": [
            ("C", 0.0, 4),
            ("D", 0.0, 4),
            ("E", 0.0, 4),
            ("F", 1.0, 4),
            ("G", 1.0, 4),
            ("B", -1.0, 4),
        ],
        "tags": ["whole_tone"],
        "constraints": {"chain_score_min": 0.95},
    },
    "quartal_stack": {
        "notes": [("C", 0.0, 4), ("F", 0.0, 4), ("B", -1.0, 4), ("E", -1.0, 5)],
        "tags": ["quartal"],
        "constraints": {"chain_score_min": 0.95},
    },
    "major_triad_closed": {
        "notes": [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)],
        "tags": ["triad", "tonal"],
    },
    "minor_triad_closed": {
        "notes": [("C", 0.0, 4), ("E", -1.0, 4), ("G", 0.0, 4)],
        "tags": ["triad", "tonal"],
    },
    "diminished_seventh": {
        "notes": [("C", 0.0, 4), ("E", -1.0, 4), ("G", -1.0, 4), ("B", -1.0, 4)],
        "tags": ["dim", "symmetric"],
    },
    "augmented_triad": {
        "notes": [("C", 0.0, 4), ("E", 0.0, 4), ("G", 1.0, 4)],
        "tags": ["aug", "symmetric"],
    },
    "octatonic_half_whole": {
        "notes": [
            ("C", 0.0, 4),
            ("C", 1.0, 4),
            ("D", 1.0, 4),
            ("E", 0.0, 4),
            ("F", 1.0, 4),
            ("G", 0.0, 4),
            ("A", 0.0, 4),
            ("B", -1.0, 4),
        ],
        "tags": ["octatonic"],
    },
    "sparse_random_like": {
        "notes": [("C", 0.0, 4), ("F", 1.0, 5), ("B", -1.0, 3), ("E", -1.0, 6)],
        "tags": ["heterogeneous"],
        "constraints": {"pair_score_max": 0.5},
    },
    "wide_span_register": {
        "notes": [("C", 0.0, 2), ("G", 0.0, 5)],
        "tags": ["wide_span"],
    },
    "dense_narrow_chromatic": {
        "notes": [
            ("C", 0.0, 4),
            ("C", 1.0, 4),
            ("D", 0.0, 4),
            ("D", 1.0, 4),
            ("E", 0.0, 4),
        ],
        "tags": ["dense", "chromatic"],
        "constraints": {"chain_score_min": 0.95, "chain_gt_pair": True},
    },
}

ALPHA = 0.6
METHOD = "dominance"
BIN = 100


def main() -> None:
    out = {
        "schema_version": 1,
        "edo": 12,
        "bin_cents": BIN,
        "homogeneity_method": METHOD,
        "headline_mode": IntervallicHeadlineMode.PAIRWISE.value,
        "hybrid_alpha": ALPHA,
        "sonorities": {},
    }
    for sid, spec in _DEFINITIONS.items():
        notes = spec["notes"]
        metrics = analyze_sonority(notes, hybrid_alpha=ALPHA, homogeneity_method=METHOD, bin_cents=BIN)
        metrics["H_headline_pairwise"] = round(float(metrics["H_headline_pairwise"]), 4)
        hybrid = resolve_headline_h(
            pair_score=metrics["pair_score"],
            chain_score=metrics["chain_score"],
            weighted_linear_score=metrics["weighted_linear_score"],
            weighted_quadratic_score=metrics["weighted_quadratic_score"],
            headline_mode=IntervallicHeadlineMode.HYBRID,
            hybrid_alpha=ALPHA,
        )
        metrics["hybrid_score"] = round(hybrid, 4)
        for k in list(metrics.keys()):
            if isinstance(metrics[k], float):
                metrics[k] = round(metrics[k], 4)
        expected = dict(metrics)
        expected["constraints"] = spec.get("constraints", {})
        out["sonorities"][sid] = {
            "description": sid.replace("_", " "),
            "tags": spec["tags"],
            "notes": [[a[0], a[1], a[2]] for a in notes],
            "expected": expected,
        }
    path = _corpus_path()
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(out['sonorities'])} sonorities)")


if __name__ == "__main__":
    main()
