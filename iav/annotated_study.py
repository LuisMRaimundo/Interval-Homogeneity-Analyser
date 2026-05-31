"""Batch study with optional human ground-truth labels (manifest-driven)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from iav.batch_analyze import BatchConfig, _analyze_one, _load_notes_from_path


@dataclass(frozen=True)
class AnnotatedCase:
    case_id: str
    source_path: Path
    human: Dict[str, Any]


def load_manifest(manifest_path: Path) -> List[AnnotatedCase]:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    cases: List[AnnotatedCase] = []
    for item in raw["cases"]:
        src = base / item["file"]
        cases.append(
            AnnotatedCase(
                case_id=str(item["id"]),
                source_path=src,
                human=dict(item.get("human_labels", {})),
            )
        )
    return cases


def run_annotated_study(
    manifest_path: Path,
    output_dir: Path,
    *,
    batch_cfg: Optional[BatchConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Run metrics on manifest cases and compare to optional human_labels.

    human_labels may include:
      - expected_headline_mode (str)
      - texture_class (str): homogeneous | heterogeneous | local_regular
      - notes (str)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = load_manifest(manifest_path)
    cfg = batch_cfg or BatchConfig(
        input_dir=manifest_path.parent,
        output_dir=output_dir,
    )
    rows: List[Dict[str, Any]] = []
    for case in cases:
        notes = _load_notes_from_path(case.source_path, cfg)
        row = _analyze_one(case.case_id, notes, cfg)
        row["human_labels"] = json.dumps(case.human, ensure_ascii=False)
        expected_mode = case.human.get("expected_headline_mode")
        if expected_mode and "error" not in row:
            row["headline_mode_match"] = row.get("headline_mode") == expected_mode
        texture = case.human.get("texture_class")
        if texture and "error" not in row:
            if texture == "local_regular":
                row["texture_match"] = row.get("chain_score", 0) > row.get("pair_score", 0)
            elif texture == "homogeneous":
                row["texture_match"] = float(row.get("headline_H", 0)) >= 0.5
            elif texture == "heterogeneous":
                row["texture_match"] = float(row.get("headline_H", 0)) < 0.5
        rows.append(row)

    out_csv = output_dir / "annotated_study_results.csv"
    if rows:
        keys: List[str] = []
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    (output_dir / "annotated_study_results.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    return rows
