#!/usr/bin/env python3
"""Exploratory inspection report for interval homogeneity regression fixtures (phase 1)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from iav.analysis_enums import IntervallicHeadlineMode
from iav.canonical_corpus import analyze_sonority, notes_from_json_rows
from iav.interval_analysis_core import dedupe_notes_by_midi, metrics_for_notes
from iav.symbolic_profile import passage_delta_rows
from iav.vertical_cardinality import vertical_cardinality_for_notes

FIXTURE_DIR = ROOT / "corpus" / "fixtures" / "interval_homogeneity_regression"
REPORT_DIR = ROOT / "corpus" / "reports"
REPORT_MD = REPORT_DIR / "interval_homogeneity_regression_inspection.md"
REPORT_JSON = REPORT_DIR / "interval_homogeneity_regression_inspection.json"


def _load_manifest() -> Dict[str, Any]:
    return json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))


def _load_fixture(fixture_id: str) -> Dict[str, Any]:
    return json.loads((FIXTURE_DIR / f"{fixture_id}.json").read_text(encoding="utf-8"))


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


def _metrics_bundle(
    notes: Sequence[Tuple[str, float, int]],
    params: Dict[str, Any],
) -> Dict[str, Any]:
    m = metrics_for_notes(
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
    analyzed = analyze_sonority(
        notes,
        hybrid_alpha=params["hybrid_alpha"],
        homogeneity_method=params["homogeneity_method"],
        bin_cents=params["bin_cents"],
        dominance_threshold=params["dominance_threshold"],
        even_high=params["even_high"],
        even_low=params["even_low"],
        chain_threshold=params["chain_threshold"],
    )
    card = vertical_cardinality_for_notes(notes, bin_cents=params["bin_cents"], edo=12)
    return {
        "cardinality": len(notes),
        "vertical_note_count": card["vertical_note_count"],
        "vertical_unique_pitch_count": card["vertical_unique_pitch_count"],
        "pair_score": round(float(m["pair_score"]), 6),
        "chain_score": round(float(m["chain_score"]), 6),
        "weighted_linear_score": round(float(m["weighted_linear_score"]), 6),
        "weighted_quadratic_score": round(float(m["weighted_quadratic_score"]), 6),
        "hybrid_score": round(float(analyzed["hybrid_score"]), 6),
        "H": round(float(m["H"]), 6),
        "H_label": str(m["H_label"]),
        "evenness_score": round(float(m["evenness_score"]), 6),
        "type_score": round(float(m["type_score"]), 6),
        "classification": str(m["classification"]),
        "distance_counts": {str(k): v for k, v in m["distance_counts"].items()},
        "adj_counts": {str(k): v for k, v in m["adj_counts"].items()},
        "dominant_pairwise_interval": analyzed.get("dominant_pairwise_interval"),
        "dominant_adjacent_interval": analyzed.get("dominant_adjacent_interval"),
        "interpretation_note": _interpretation_note(payload_id="", m=m, analyzed=analyzed),
    }


def _interpretation_note(*, payload_id: str, m: Dict[str, Any], analyzed: Dict[str, Any]) -> str:
    pair = float(m["pair_score"])
    chain = float(m["chain_score"])
    if pair >= 0.99 and chain >= 0.99:
        return "Single-interval or maximally concentrated dyad/degenerate case (not consonance validation)."
    if chain > pair + 0.05:
        return "Adjacent regularity exceeds pairwise concentration under current semantics."
    if pair > chain + 0.05:
        return "Pairwise concentration exceeds adjacent regularity."
    return "Mixed interval distribution; read H only with full interval profile context."


def _inspect_single_fixture(fixture_id: str) -> Dict[str, Any]:
    payload = _load_fixture(fixture_id)
    params = _analysis_params(payload)
    row: Dict[str, Any] = {
        "fixture": fixture_id,
        "description": payload.get("description"),
        "tags": payload.get("tags", []),
        "analysis": params,
    }

    if "slices" in payload:
        slice_rows: List[Dict[str, Any]] = []
        summary_rows: List[Dict[str, Any]] = []
        for sl in payload["slices"]:
            notes = notes_from_json_rows(sl["notes"])
            metrics = _metrics_bundle(notes, params)
            metrics["slice_id"] = sl["slice_id"]
            metrics["label"] = sl["label"]
            metrics["notes"] = sl["notes"]
            metrics["interpretation_note"] = _interpretation_note(
                payload_id=fixture_id, m=metrics, analyzed={"hybrid_score": metrics["hybrid_score"]}
            )
            slice_rows.append(metrics)
            summary_rows.append(
                {
                    "Slice": sl["slice_id"],
                    "Label": sl["label"],
                    "H (interval dominance)": metrics["H"],
                }
            )
        row["slices"] = slice_rows
        row["passage_delta_rows"] = passage_delta_rows(summary_rows)
        row["interval_profile_changes"] = len({json.dumps(s["distance_counts"]) for s in slice_rows}) > 1
        return row

    if fixture_id == "EDO_bin_change_sensitivity":
        notes = notes_from_json_rows(payload["notes"])
        variants: List[Dict[str, Any]] = []
        for bin_cents in payload.get("bin_variants", [100, 50]):
            p = {**params, "bin_cents": int(bin_cents)}
            metrics = _metrics_bundle(notes, p)
            metrics["bin_cents"] = bin_cents
            metrics["interpretation_note"] = (
                f"Observed at bin_cents={bin_cents}; binning is a modelling choice, not tuning."
            )
            variants.append(metrics)
        row["bin_variants"] = variants
        row["labels_or_metrics_differ"] = any(
            variants[0]["H"] != v["H"] or variants[0]["distance_counts"] != v["distance_counts"]
            for v in variants[1:]
        )
        return row

    notes = notes_from_json_rows(payload["notes"])
    row["notes"] = payload["notes"]
    metrics = _metrics_bundle(notes, params)
    metrics["interpretation_note"] = _interpretation_note(
        payload_id=fixture_id,
        m=metrics,
        analyzed={"hybrid_score": metrics["hybrid_score"]},
    )
    row.update(metrics)

    if fixture_id == "repeated_pitch_density_not_homogeneity":
        deduped = dedupe_notes_by_midi(notes, bin_cents=params["bin_cents"])
        row["deduped_note_count"] = len(deduped)
        row["deduped_metrics"] = _metrics_bundle(deduped, params)

    if payload.get("reference_fixture"):
        ref_notes = notes_from_json_rows(_load_fixture(payload["reference_fixture"])["notes"])
        ref_metrics = _metrics_bundle(ref_notes, params)
        row["reference_fixture"] = payload["reference_fixture"]
        row["reference_metrics"] = ref_metrics

    return row


def _render_markdown(rows: List[Dict[str, Any]], generated_at: str) -> str:
    lines = [
        "# Interval homogeneity regression — exploratory inspection (phase 1)",
        "",
        f"Generated: {generated_at}",
        "",
        "These values are **exploratory** only. Do not promote them to strict golden references.",
        "",
    ]
    for row in rows:
        lines.append(f"## {row['fixture']}")
        lines.append("")
        lines.append(f"**Description:** {row.get('description', '')}")
        lines.append("")
        if "slices" in row:
            for sl in row["slices"]:
                lines.append(f"### Slice {sl['slice_id']}: {sl['label']}")
                lines.append(f"- Notes: `{sl['notes']}`")
                lines.append(f"- H: {sl['H']}; pair_score: {sl['pair_score']}; chain_score: {sl['chain_score']}")
                lines.append(f"- hybrid_score: {sl['hybrid_score']}; evenness: {sl['evenness_score']}")
                lines.append(f"- Note: {sl['interpretation_note']}")
                lines.append("")
            lines.append(f"- interval_profile_changes: {row.get('interval_profile_changes')}")
            lines.append("")
            continue
        if "bin_variants" in row:
            for variant in row["bin_variants"]:
                lines.append(f"### bin_cents={variant['bin_cents']}")
                lines.append(f"- H: {variant['H']}; pair_score: {variant['pair_score']}; chain_score: {variant['chain_score']}")
                lines.append(f"- distance_counts: {variant['distance_counts']}")
                lines.append("")
            continue
        lines.append(f"- Notes: `{row.get('notes')}`")
        lines.append(f"- Cardinality: {row.get('cardinality')}; unique pitches: {row.get('vertical_unique_pitch_count')}")
        lines.append(f"- pair_score: {row.get('pair_score')}; chain_score: {row.get('chain_score')}")
        lines.append(f"- weighted_linear_score: {row.get('weighted_linear_score')}")
        lines.append(f"- hybrid_score: {row.get('hybrid_score')}; H: {row.get('H')}; H_label: {row.get('H_label')}")
        lines.append(f"- evenness_score: {row.get('evenness_score')}; classification: {row.get('classification')}")
        lines.append(f"- distance_counts: {row.get('distance_counts')}")
        lines.append(f"- adj_counts: {row.get('adj_counts')}")
        lines.append(f"- Note: {row.get('interpretation_note')}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    manifest = _load_manifest()
    fixture_ids: List[str] = list(manifest["fixtures"])
    rows = [_inspect_single_fixture(fid) for fid in fixture_ids]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": generated_at,
        "suite": "interval_homogeneity_regression",
        "phase": 1,
        "fixture_count": len(rows),
        "fixtures": rows,
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(_render_markdown(rows, generated_at), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    print(f"Wrote {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
