"""Structured aggregate homogeneity / interval-count results (replaces untyped dict-only flow)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AggregateHomogeneityMetrics:
    """
    All quantities returned by ``metrics_for_notes``.

    Mapping-style access (``m["total_intervals"]``, ``"key" in m``, ``m.get(...)``) is supported
    for backward compatibility with tests and older call sites.
    """

    H: Optional[float]
    chain_score: Optional[float]
    pair_score: Optional[float]
    weighted_linear_score: Optional[float]
    weighted_quadratic_score: Optional[float]
    intervallic_headline_mode: str
    hybrid_alpha_used: float
    H_dom: Optional[float]
    chain_dom: Optional[float]
    pair_dom: Optional[float]
    H_ent: Optional[float]
    chain_ent: Optional[float]
    pair_ent: Optional[float]
    weighted_linear_dom: Optional[float]
    weighted_quadratic_dom: Optional[float]
    weighted_linear_ent: Optional[float]
    weighted_quadratic_ent: Optional[float]
    H_consensus: Optional[float]
    interval_counts: Dict[str, int]
    distance_counts: Dict[int, int]
    adj_counts: Dict[int, int]
    total_intervals: int
    type_score: float
    evenness_score: float
    classification: str
    H_label: str
    compactness_score: float
    pitch_span: int
    avg_distance: float
    top_pair_label: Optional[str]
    top_pair_semi_count: int
    top_pair_semi_share: float
    top_chain_label: Optional[str]
    top_chain_semi_count: int
    top_chain_semi_share: float
    pairwise_entropy_support_bins: int
    blend_chain_in_h: bool
    H_primary_title: str
    H_primary_help: str
    pair_metric_title: str
    chain_metric_title: str
    weighted_linear_metric_title: str
    weighted_quadratic_metric_title: str
    evenness_title: str

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as exc:
            raise KeyError(key) from exc

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and hasattr(self, key)

    def as_dict(self) -> Dict[str, Any]:
        """Plain dict (e.g. for serialization or legacy APIs)."""
        return asdict(self)
