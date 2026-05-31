"""Assemble per-aggregate metric dicts for UI and export."""

from __future__ import annotations

import math
from typing import Dict, Sequence, Union

from iav.aggregate_metrics import AggregateHomogeneityMetrics
from iav.analysis_enums import (
    HomogeneityMethod,
    IntervallicHeadlineMode,
    homogeneity_method_from_str,
    intervallic_headline_mode_from_str,
)
from iav.note_types import NoteTuple

from ._edo_labels import units_to_label
from ._homogeneity import (
    classify_aggregate,
    cluster_compactness,
    dominant_item,
    entropy_evenness_supportbounded,
    h_band_label,
    homogeneity_score,
    pairwise_distance_support_bins,
    type_concentration,
)

_HomogeneityMethodArg = Union[HomogeneityMethod, str]
_HeadlineModeArg = Union[IntervallicHeadlineMode, str, None]

_HEADLINE_TITLES: Dict[IntervallicHeadlineMode, tuple[str, str]] = {
    IntervallicHeadlineMode.PAIRWISE: (
        "Pairwise intervallic concentration (headline H)",
        "Concentration of all unordered absolute pitch-distance pairs on the analysis grid.",
    ),
    IntervallicHeadlineMode.ADJACENT: (
        "Adjacent intervallic regularity (headline H)",
        "Concentration of intervals between consecutive pitches after sorting by height "
        "(generative / local regularity).",
    ),
    IntervallicHeadlineMode.WEIGHTED_LINEAR: (
        "Proximity-weighted intervallic homogeneity (headline H, 1/|i−j|)",
        "All pairs weighted by 1/ordinal separation after sorting; nearby pairs dominate.",
    ),
    IntervallicHeadlineMode.WEIGHTED_QUADRATIC: (
        "Proximity-weighted intervallic homogeneity (headline H, 1/|i−j|²)",
        "Stronger emphasis on locally adjacent pitch pairs than the linear weights.",
    ),
    IntervallicHeadlineMode.HYBRID: (
        "Hybrid intervallic homogeneity (headline H)",
        "α·adjacent regularity + (1−α)·pairwise concentration; α is hybrid weight on adjacent.",
    ),
}


def _unpack_homogeneity(result: tuple) -> tuple:
    """Support legacy 6-tuples and extended 10-tuples from homogeneity_score."""
    if len(result) >= 10:
        return (
            result[0],
            result[1],
            result[2],
            result[3],
            result[4],
            result[5],
            result[6],
            result[7],
        )
    h, chain, pair, ic, dc, adj = result[:6]
    return h, chain, pair, ic, dc, adj, pair, pair


def metrics_for_notes(
    notes: Sequence[NoteTuple],
    dominance_threshold: float,
    even_high: float,
    even_low: float,
    alpha_used: float,
    homogeneity_method: _HomogeneityMethodArg,
    bin_cents: int = 100,
    chain_threshold: float = 0.60,
    *,
    blend_chain_in_h: bool = False,
    intervallic_headline_mode: _HeadlineModeArg = None,
) -> AggregateHomogeneityMetrics:
    """
      Build UI/export metrics for one aggregate.

      Always reports pairwise concentration, adjacent regularity, and both proximity-weighted
    scores; headline H follows ``intervallic_headline_mode`` (default: pairwise).
    """
    hm = homogeneity_method_from_str(homogeneity_method)
    if intervallic_headline_mode is None:
        headline_mode = (
            IntervallicHeadlineMode.HYBRID if blend_chain_in_h else IntervallicHeadlineMode.PAIRWISE
        )
    else:
        headline_mode = intervallic_headline_mode_from_str(intervallic_headline_mode)

    support_bins = pairwise_distance_support_bins(notes, bin_cents)

    def _run(method: str) -> tuple:
        return _unpack_homogeneity(
            homogeneity_score(
                notes,
                alpha=alpha_used,
                method=method,
                bin_cents=bin_cents,
                blend_chain_in_h=False,
                headline_mode=headline_mode,
            )
        )

    if hm == HomogeneityMethod.COMBINED:
        (
            h_dom,
            chain_dom,
            pair_dom,
            interval_counts,
            distance_counts,
            adj_counts,
            w_lin_dom,
            w_quad_dom,
        ) = _run(HomogeneityMethod.DOMINANCE.value)
        h_ent, chain_ent, pair_ent, _, _, _, w_lin_ent, w_quad_ent = _run(
            HomogeneityMethod.ENTROPY.value
        )
        h_consensus = math.sqrt(max(0.0, h_dom) * max(0.0, h_ent))
        h_for_band = h_consensus
        chain_for_classify = chain_dom
        chain_score = chain_dom
        pair_score = pair_dom
        weighted_linear_score = w_lin_dom
        weighted_quadratic_score = w_quad_dom
    else:
        h_dom = None
        chain_dom = None
        pair_dom = None
        h_ent = None
        chain_ent = None
        pair_ent = None
        h_consensus = None
        w_lin_ent = None
        w_quad_ent = None
        method_value = hm.value
        (
            h_for_band,
            chain_score,
            pair_score,
            interval_counts,
            distance_counts,
            adj_counts,
            weighted_linear_score,
            weighted_quadratic_score,
        ) = _run(method_value)
        if hm == HomogeneityMethod.ENTROPY:
            h_ent, chain_ent, pair_ent = h_for_band, chain_score, pair_score
            w_lin_ent, w_quad_ent = weighted_linear_score, weighted_quadratic_score
            h_dom = None
            chain_dom = None
            pair_dom = None
            chain_for_classify = chain_ent
        else:
            h_dom, chain_dom, pair_dom = h_for_band, chain_score, pair_score
            chain_for_classify = chain_dom

    total_intervals = sum(interval_counts.values())
    type_score = type_concentration(interval_counts)
    evenness_score = (
        entropy_evenness_supportbounded(distance_counts, support_bins) if distance_counts else 0.0
    )

    classification = classify_aggregate(
        interval_counts,
        dominance_threshold=dominance_threshold,
        even_high=even_high,
        even_low=even_low,
        chain_dominance=chain_for_classify,
        chain_threshold=chain_threshold,
        pairwise_abs_evenness=evenness_score,
    )
    h_label = h_band_label(float(h_for_band) if h_for_band is not None else 0.0)
    compactness_score, pitch_span, avg_distance = cluster_compactness(notes, bin_cents=bin_cents)
    top_pair_semi, top_pair_semi_count, top_pair_semi_share = dominant_item(distance_counts)
    top_pair_label = units_to_label(top_pair_semi, bin_cents) if top_pair_semi is not None else None
    top_chain_semi, top_chain_semi_count, top_chain_semi_share = dominant_item(adj_counts)
    top_chain_label = (
        units_to_label(top_chain_semi, bin_cents) if top_chain_semi is not None else None
    )

    h_primary_title, h_primary_help = _HEADLINE_TITLES[headline_mode]
    if headline_mode == IntervallicHeadlineMode.HYBRID:
        h_primary_help += f" Current α = {alpha_used:.2f} on adjacent."

    even_title = (
        "Pairwise absolute-distance evenness (Shannon / ln(span+1), same bins as distance_counts)"
    )
    if hm == HomogeneityMethod.COMBINED:
        metric_titles = {
            "H_primary_title": "Composite homogeneity (consensus heuristic)",
            "H_primary_help": (
                "Geometric mean of dominance- and entropy-concentration headline H values "
                f"for mode «{headline_mode.value}»; exploratory."
            ),
            "pair_metric_title": "Pairwise intervallic concentration (dominance / entropy)",
            "chain_metric_title": "Adjacent intervallic regularity (dominance / entropy)",
            "weighted_linear_metric_title": "Proximity-weighted (1/|i−j|) concentration",
            "weighted_quadratic_metric_title": "Proximity-weighted (1/|i−j|²) concentration",
            "evenness_title": even_title,
        }
    elif hm == HomogeneityMethod.ENTROPY:
        metric_titles = {
            "H_primary_title": h_primary_title,
            "H_primary_help": h_primary_help + " Entropy concentration path (span-normalized).",
            "pair_metric_title": "Pairwise intervallic concentration (entropy)",
            "chain_metric_title": "Adjacent intervallic regularity (entropy)",
            "weighted_linear_metric_title": "Proximity-weighted linear (entropy)",
            "weighted_quadratic_metric_title": "Proximity-weighted quadratic (entropy)",
            "evenness_title": even_title,
        }
    else:
        metric_titles = {
            "H_primary_title": h_primary_title,
            "H_primary_help": h_primary_help + " Dominance (max share) path.",
            "pair_metric_title": "Pairwise intervallic concentration (dominance)",
            "chain_metric_title": "Adjacent intervallic regularity (dominance)",
            "weighted_linear_metric_title": "Proximity-weighted linear (dominance)",
            "weighted_quadratic_metric_title": "Proximity-weighted quadratic (dominance)",
            "evenness_title": even_title,
        }

    return AggregateHomogeneityMetrics(
        H=h_for_band,
        chain_score=chain_score,
        pair_score=pair_score,
        weighted_linear_score=weighted_linear_score,
        weighted_quadratic_score=weighted_quadratic_score,
        intervallic_headline_mode=headline_mode.value,
        hybrid_alpha_used=alpha_used,
        H_dom=h_dom,
        chain_dom=chain_dom,
        pair_dom=pair_dom,
        H_ent=h_ent,
        chain_ent=chain_ent,
        pair_ent=pair_ent,
        weighted_linear_dom=w_lin_dom if hm == HomogeneityMethod.COMBINED else None,
        weighted_quadratic_dom=w_quad_dom if hm == HomogeneityMethod.COMBINED else None,
        weighted_linear_ent=w_lin_ent if hm == HomogeneityMethod.COMBINED else None,
        weighted_quadratic_ent=w_quad_ent if hm == HomogeneityMethod.COMBINED else None,
        H_consensus=h_consensus,
        interval_counts=interval_counts,
        distance_counts=distance_counts,
        adj_counts=adj_counts,
        total_intervals=total_intervals,
        type_score=type_score,
        evenness_score=evenness_score,
        classification=classification,
        H_label=h_label,
        compactness_score=compactness_score,
        pitch_span=pitch_span,
        avg_distance=avg_distance,
        top_pair_label=top_pair_label,
        top_pair_semi_count=top_pair_semi_count,
        top_pair_semi_share=top_pair_semi_share,
        top_chain_label=top_chain_label,
        top_chain_semi_count=top_chain_semi_count,
        top_chain_semi_share=top_chain_semi_share,
        pairwise_entropy_support_bins=support_bins,
        blend_chain_in_h=blend_chain_in_h or headline_mode == IntervallicHeadlineMode.HYBRID,
        **metric_titles,
    )
