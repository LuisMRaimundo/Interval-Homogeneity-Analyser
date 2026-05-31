"""Canonical sonority reference corpus (frozen expected metrics for regression)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from iav.analysis_enums import IntervallicHeadlineMode
from iav.interval_analysis_core import (
    homogeneity_score,
    metrics_for_notes,
    set_class_summary_12tet,
)
from iav.interval_analysis_core._edo_labels import units_to_label
from iav.interval_analysis_core._homogeneity import dominant_item, resolve_headline_h
from iav.note_types import NoteTuple

_CORPUS_FILENAME = "canonical_sonorities.json"
_DEFAULT_TOLERANCE = 1e-3


@dataclass(frozen=True)
class CorpusConfig:
    schema_version: int
    edo: int
    bin_cents: int
    homogeneity_method: str
    hybrid_alpha: float
    headline_mode: str


@dataclass(frozen=True)
class SonoritySpec:
    sonority_id: str
    description: str
    tags: Tuple[str, ...]
    notes: Tuple[NoteTuple, ...]
    expected: Mapping[str, Any]


def _corpus_path() -> Path:
    return Path(__file__).resolve().parent / "data" / _CORPUS_FILENAME


def load_canonical_corpus(
    path: Optional[Path] = None,
) -> Tuple[CorpusConfig, Dict[str, SonoritySpec]]:
    """Load bundled or custom canonical sonorities JSON."""
    p = path or _corpus_path()
    raw = json.loads(p.read_text(encoding="utf-8"))
    cfg = CorpusConfig(
        schema_version=int(raw["schema_version"]),
        edo=int(raw["edo"]),
        bin_cents=int(raw["bin_cents"]),
        homogeneity_method=str(raw["homogeneity_method"]),
        hybrid_alpha=float(raw["hybrid_alpha"]),
        headline_mode=str(raw.get("headline_mode", "pairwise_intervallic_concentration")),
    )
    specs: Dict[str, SonoritySpec] = {}
    for sid, block in raw["sonorities"].items():
        notes = tuple((str(n[0]), float(n[1]), int(n[2])) for n in block["notes"])
        specs[sid] = SonoritySpec(
            sonority_id=sid,
            description=str(block.get("description", sid)),
            tags=tuple(block.get("tags", [])),
            notes=notes,
            expected=block["expected"],
        )
    return cfg, specs


def notes_from_json_rows(rows: Sequence[Sequence[Any]]) -> List[NoteTuple]:
    return [(str(r[0]), float(r[1]), int(r[2])) for r in rows]


def analyze_sonority(
    notes: Sequence[NoteTuple],
    *,
    hybrid_alpha: float = 0.6,
    homogeneity_method: str = "dominance",
    bin_cents: int = 100,
    dominance_threshold: float = 0.35,
    even_high: float = 0.8,
    even_low: float = 0.3,
    chain_threshold: float = 0.60,
) -> Dict[str, Any]:
    """Compute the canonical metric bundle for one aggregate."""
    m = metrics_for_notes(
        notes,
        dominance_threshold,
        even_high,
        even_low,
        hybrid_alpha,
        homogeneity_method,
        bin_cents=bin_cents,
        chain_threshold=chain_threshold,
        intervallic_headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    h, chain, pair, _ic, dc, adj, w_lin, w_quad, *_ = homogeneity_score(
        notes,
        hybrid_alpha,
        homogeneity_method,
        bin_cents,
        headline_mode=IntervallicHeadlineMode.PAIRWISE,
    )
    hybrid = resolve_headline_h(
        pair_score=pair,
        chain_score=chain,
        weighted_linear_score=w_lin,
        weighted_quadratic_score=w_quad,
        headline_mode=IntervallicHeadlineMode.HYBRID,
        hybrid_alpha=hybrid_alpha,
    )
    tp, _tc, ts = dominant_item(dc)
    ta, _tac, tas = dominant_item(adj)
    pc = set_class_summary_12tet(notes)
    return {
        "pair_score": float(pair),
        "chain_score": float(chain),
        "weighted_linear_score": float(w_lin),
        "weighted_quadratic_score": float(w_quad),
        "hybrid_score": float(hybrid),
        "H_headline_pairwise": float(m["H"]),
        "dominant_pairwise_interval": units_to_label(tp, bin_cents) if tp is not None else None,
        "dominant_pairwise_share": float(ts),
        "dominant_adjacent_interval": units_to_label(ta, bin_cents) if ta is not None else None,
        "dominant_adjacent_share": float(tas),
        "interval_vector": pc["interval_vector"] if pc else None,
        "interval_vector_str": pc["interval_vector_str"] if pc else None,
        "classification": str(m["classification"]),
        "H_label": str(m["H_label"]),
    }


def _assert_close(actual: float, expected: float, tol: float, field: str, sid: str) -> None:
    if abs(actual - expected) > tol:
        raise AssertionError(
            f"{sid}.{field}: got {actual:.6f}, expected {expected:.6f} (tol={tol})"
        )


def verify_sonority_metrics(
    computed: Mapping[str, Any],
    expected: Mapping[str, Any],
    sonority_id: str,
    *,
    tolerance: float = _DEFAULT_TOLERANCE,
) -> None:
    """Assert computed metrics match frozen expectations and optional constraints."""
    if "H_headline_pairwise" in expected and expected["H_headline_pairwise"] is not None:
        headline = float(computed.get("H_headline_pairwise", computed.get("pair_score", 0)))
        _assert_close(
            headline,
            float(expected["H_headline_pairwise"]),
            tolerance,
            "H_headline_pairwise",
            sonority_id,
        )
        assert abs(headline - float(computed["pair_score"])) < tolerance, (
            f"{sonority_id}: headline pairwise H must match pair_score under preset defaults"
        )

    for key in (
        "pair_score",
        "chain_score",
        "weighted_linear_score",
        "weighted_quadratic_score",
        "hybrid_score",
        "dominant_pairwise_share",
        "dominant_adjacent_share",
    ):
        if key in expected and expected[key] is not None:
            _assert_close(float(computed[key]), float(expected[key]), tolerance, key, sonority_id)

    for key in (
        "dominant_pairwise_interval",
        "dominant_adjacent_interval",
        "interval_vector",
        "interval_vector_str",
        "classification",
        "H_label",
    ):
        if key in expected and expected[key] is not None:
            assert computed[key] == expected[key], (
                f"{sonority_id}.{key}: got {computed[key]!r}, expected {expected[key]!r}"
            )

    constraints = expected.get("constraints") or {}
    if constraints.get("chain_score_min") is not None:
        assert computed["chain_score"] >= float(constraints["chain_score_min"]), sonority_id
    if constraints.get("pair_score_max") is not None:
        assert computed["pair_score"] <= float(constraints["pair_score_max"]), sonority_id
    if constraints.get("pair_score_min") is not None:
        assert computed["pair_score"] >= float(constraints["pair_score_min"]), sonority_id
    if constraints.get("chain_gt_pair"):
        assert computed["chain_score"] > computed["pair_score"], sonority_id


def bundled_corpus_resource() -> str:
    """Path-like resource id for documentation."""
    return f"iav.data:{_CORPUS_FILENAME}"


def export_corpus_json(path: Path) -> None:
    """Copy bundled corpus to disk (for examples/)."""
    path.write_text(_corpus_path().read_text(encoding="utf-8"), encoding="utf-8")
