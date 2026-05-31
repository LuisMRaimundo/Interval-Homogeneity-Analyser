"""Batch export and AggregateHomogeneityMetrics schema stability."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from iav.aggregate_metrics import AggregateHomogeneityMetrics
from iav.batch_analyze import BatchConfig, run_batch
from iav.interval_analysis_core import metrics_for_notes

ROOT = Path(__file__).resolve().parent.parent

_REQUIRED_METRIC_FIELDS = frozenset(
    {
        "H",
        "H_label",
        "pair_score",
        "chain_score",
        "weighted_linear_score",
        "weighted_quadratic_score",
        "evenness_score",
        "interval_counts",
        "distance_counts",
        "adj_counts",
        "intervallic_headline_mode",
        "hybrid_alpha_used",
        "total_intervals",
        "classification",
    }
)


def test_aggregate_homogeneity_metrics_dataclass_fields():
    names = {f.name for f in dataclasses.fields(AggregateHomogeneityMetrics)}
    assert _REQUIRED_METRIC_FIELDS <= names


def test_metrics_mapping_access():
    notes = [("C", 0.0, 4), ("E", 0.0, 4), ("G", 0.0, 4)]
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.6, "dominance", bin_cents=100)
    for key in _REQUIRED_METRIC_FIELDS:
        assert key in m
        assert key in m.as_dict()


def test_batch_results_json_schema_keys(tmp_path):
    cfg = BatchConfig(
        input_dir=ROOT / "examples" / "corpus",
        output_dir=tmp_path / "out",
    )
    result = run_batch(cfg)
    assert "results" in result
    row = next(r for r in result["results"] if "headline_H" in r)
    for key in ("source_id", "note_count", "headline_H", "H_label", "pair_score", "chain_score"):
        assert key in row
    payload = json.loads((tmp_path / "out" / "results.json").read_text(encoding="utf-8"))
    assert "config" in payload
    assert "results" in payload
    assert (tmp_path / "out" / "config_used.json").is_file()
