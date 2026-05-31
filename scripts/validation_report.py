#!/usr/bin/env python3
"""Validation summary: human annotations vs tool classification (symbolic protocol)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_TEXTURE_CLASSES = ("homogeneous", "heterogeneous", "local_regular")


def _load_annotations(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("annotation CSV has no header")
        required = {"case_id", "texture_class", "rater_id"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"annotation CSV missing columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def _load_metrics_json(path: Path) -> Dict[str, Dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("results", raw if isinstance(raw, list) else [])
    if not isinstance(rows, list):
        raise ValueError("metrics JSON must contain a 'results' list or be a list")
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        cid = str(row.get("source_id") or row.get("case_id") or "")
        if cid:
            out[cid] = row
    return out


def _classification_to_texture_proxy(classification: str) -> str:
    """Map tool classification string to coarse texture proxy for confusion matrix."""
    c = (classification or "").lower()
    if "uniform stacking" in c or "-dominant" in c:
        return "homogeneous"
    if "irregular stacking" in c or "no dominant" in c:
        return "heterogeneous"
    return "local_regular"


def _cohen_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> Optional[float]:
    if len(labels_a) != len(labels_b) or not labels_a:
        return None
    categories = sorted(set(labels_a) | set(labels_b))
    n = len(labels_a)
    agree = sum(1 for x, y in zip(labels_a, labels_b) if x == y)
    p_o = agree / n
    count_a = Counter(labels_a)
    count_b = Counter(labels_b)
    p_e = sum((count_a.get(c, 0) / n) * (count_b.get(c, 0) / n) for c in categories)
    if abs(1.0 - p_e) < 1e-12:
        return None
    return (p_o - p_e) / (1.0 - p_e)


def _spearman_rho(x: Sequence[float], y: Sequence[float]) -> Tuple[Optional[float], str]:
    try:
        from scipy.stats import spearmanr  # type: ignore[import-untyped]
    except ImportError:
        return None, "scipy not installed; Spearman correlation skipped"
    if len(x) < 2 or len(y) < 2 or len(x) != len(y):
        return None, "insufficient paired numeric rows for Spearman"
    rho, _ = spearmanr(x, y)
    return float(rho), "ok"


def _confusion_matrix(
    human: Sequence[str], tool_proxy: Sequence[str]
) -> Dict[str, Dict[str, int]]:
    matrix: Dict[str, Dict[str, int]] = {h: {t: 0 for t in _TEXTURE_CLASSES} for h in _TEXTURE_CLASSES}
    for h, t in zip(human, tool_proxy):
        hh = h if h in matrix else "heterogeneous"
        tt = t if t in matrix[hh] else "local_regular"
        matrix[hh][tt] += 1
    return matrix


def build_validation_summary(
    annotations: Sequence[Mapping[str, str]],
    metrics_by_case: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    """Join annotations to metrics and compute protocol statistics."""
    by_case_raters: Dict[str, List[Mapping[str, str]]] = defaultdict(list)
    for row in annotations:
        by_case_raters[str(row["case_id"])].append(row)

    joined: List[Dict[str, Any]] = []
    human_labels: List[str] = []
    tool_labels: List[str] = []
    headline_h: List[float] = []
    human_ordinal: List[float] = []

    ordinal_map = {"heterogeneous": 0.0, "local_regular": 0.5, "homogeneous": 1.0}

    for case_id, rows in sorted(by_case_raters.items()):
        metric = metrics_by_case.get(case_id, {})
        classification = str(metric.get("classification") or "")
        tool_proxy = _classification_to_texture_proxy(classification)
        h_val = metric.get("headline_H", metric.get("H"))
        for row in rows:
            human = str(row["texture_class"]).strip().lower()
            rec = {
                "case_id": case_id,
                "rater_id": row["rater_id"],
                "texture_class_human": human,
                "texture_class_tool_proxy": tool_proxy,
                "classification": classification,
                "headline_H": h_val,
                "H_label": metric.get("H_label"),
                "notes": row.get("notes", ""),
            }
            joined.append(rec)
            human_labels.append(human)
            tool_labels.append(tool_proxy)
            if h_val is not None:
                try:
                    headline_h.append(float(h_val))
                    human_ordinal.append(ordinal_map.get(human, 0.5))
                except (TypeError, ValueError):
                    pass

    kappa_pairs: List[Dict[str, Any]] = []
    for case_id, rows in by_case_raters.items():
        if len(rows) == 2:
            a, b = rows[0], rows[1]
            ka = str(a["texture_class"]).strip().lower()
            kb = str(b["texture_class"]).strip().lower()
            k = _cohen_kappa([ka], [kb])
            if k is not None:
                kappa_pairs.append(
                    {
                        "case_id": case_id,
                        "rater_a": a["rater_id"],
                        "rater_b": b["rater_id"],
                        "kappa": k,
                    }
                )

    kappa_global: Optional[float] = None
    dual_cases = [c for c, rs in by_case_raters.items() if len(rs) == 2]
    if dual_cases:
        la = [str(by_case_raters[c][0]["texture_class"]).strip().lower() for c in dual_cases]
        lb = [str(by_case_raters[c][1]["texture_class"]).strip().lower() for c in dual_cases]
        kappa_global = _cohen_kappa(la, lb)

    rho, rho_note = _spearman_rho(human_ordinal, headline_h)

    return {
        "n_annotations": len(annotations),
        "n_cases": len(by_case_raters),
        "human_texture_counts": dict(Counter(human_labels)),
        "tool_proxy_counts": dict(Counter(tool_labels)),
        "confusion_matrix_human_rows_tool_cols": _confusion_matrix(human_labels, tool_labels),
        "cohen_kappa_global_two_raters": kappa_global,
        "cohen_kappa_per_pair": kappa_pairs,
        "spearman_human_ordinal_vs_headline_H": rho,
        "spearman_note": rho_note,
        "joined_rows": joined,
    }


def write_validation_outputs(summary: Mapping[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "validation_summary.json"
    serializable = {k: v for k, v in summary.items() if k != "joined_rows"}
    serializable["joined_rows"] = list(summary.get("joined_rows", []))
    json_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")

    csv_path = output_dir / "validation_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "rater_id",
                "texture_class_human",
                "texture_class_tool_proxy",
                "classification",
                "headline_H",
                "H_label",
                "notes",
            ],
        )
        writer.writeheader()
        for row in summary.get("joined_rows", []):
            writer.writerow(row)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path, help="Annotation CSV path")
    parser.add_argument(
        "--metrics",
        type=Path,
        default=None,
        help="Batch results.json (optional; inline metrics used if omitted)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for validation_summary.json/csv",
    )
    args = parser.parse_args(argv)

    annotations = _load_annotations(args.annotations)
    if args.metrics is not None:
        metrics_by_case = _load_metrics_json(args.metrics)
    else:
        metrics_by_case = {}

    summary = build_validation_summary(annotations, metrics_by_case)
    write_validation_outputs(summary, args.output)
    print(f"Wrote {args.output / 'validation_summary.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
