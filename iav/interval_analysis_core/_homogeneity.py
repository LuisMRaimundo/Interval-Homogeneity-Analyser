"""Homogeneity heuristics, distribution summaries, and aggregate classification."""

from __future__ import annotations

import itertools
import math
from typing import Any, Dict, Mapping, Optional, Sequence, Union

from iav.analysis_enums import IntervallicHeadlineMode
from iav.note_types import NoteTuple

from ._edo_labels import intervals_for_notes, note_to_units


def cluster_compactness(notes: Sequence[NoteTuple], bin_cents: int = 100):
    if len(notes) < 2:
        return 1.0, 0, 0.0
    units = [note_to_units(letter, alter, octave, bin_cents) for letter, alter, octave in notes]
    min_units = min(units)
    max_units = max(units)
    span_units = max_units - min_units
    if span_units == 0:
        return 1.0, 0, 0.0
    total = 0.0
    count = 0
    for lower, upper in itertools.combinations(units, 2):
        total += abs(upper - lower)
        count += 1
    avg_distance = total / count
    compactness = 1.0 - (avg_distance / span_units)
    return compactness, span_units * bin_cents, avg_distance * bin_cents


def type_concentration(interval_counts: Dict[str, int]):
    if not interval_counts:
        return 0.0
    total = sum(interval_counts.values())
    num_types = len(interval_counts)
    if total <= 1:
        return 1.0
    return 1.0 - (num_types - 1) / (total - 1)


def entropy_evenness(interval_counts: Dict[str, int]):
    """
    Normalized Shannon entropy of category proportions (0..1), treating counts as a distribution.

    **Pielou-style** denominator **ln(K)** with **K** = number of categories (dict keys), each with
    positive count in normal use. Exploratory only; not used for headline entropy concentration or
    ``evenness_score`` in the production pipeline (those use ``entropy_evenness_supportbounded``;
    see ``TECHNICAL_MANUAL.md`` §4.4). Used as **fallback** in ``classify_aggregate`` when the
    caller omits ``pairwise_abs_evenness``. For pairwise **absolute** distance histograms prefer
    ``entropy_evenness_supportbounded`` with support from ``pairwise_distance_support_bins``.
    """
    if not interval_counts:
        return 0.0
    total = sum(interval_counts.values())
    counts = list(interval_counts.values())
    if len(counts) == 1:
        return 0.0
    entropy = 0.0
    for c in counts:
        p = c / total
        if p > 0:
            entropy -= p * math.log(p)
    max_entropy = math.log(len(counts))
    return 1.0 if max_entropy == 0 else entropy / max_entropy


def pairwise_pitch_span_units(notes: Sequence[NoteTuple], bin_cents: int = 100) -> int:
    """Max − min pitch in analysis units (same grid as ``distance_counts`` keys; see §4.4 in ``TECHNICAL_MANUAL.md``)."""
    if len(notes) < 2:
        return 0
    units = [note_to_units(letter, alter, octave, bin_cents) for letter, alter, octave in notes]
    return int(max(units) - min(units))


def pairwise_distance_support_bins(notes: Sequence[NoteTuple], bin_cents: int = 100) -> int:
    """
    Returns ``max(1, span + 1)`` where ``span`` is ``pairwise_pitch_span_units`` — cardinality of
    integer absolute-distance bins ``0..span`` for pitches confined to the observed register (in
    ``note_to_units`` steps). Passed as ``support_bins`` into ``entropy_evenness_supportbounded``
    for production entropy concentration (``TECHNICAL_MANUAL.md`` §4.4).
    """
    span = pairwise_pitch_span_units(notes, bin_cents)
    return max(1, span + 1)


def entropy_evenness_supportbounded(counts: Dict[Any, int], support_bins: int) -> float:
    """
    Shannon entropy of the empirical category distribution, normalized by **ln(max(1, k))**
    with ``k = int(support_bins)`` clamped to at least **1** in code (equivalently
    **ln(max(1, support_bins))** for integer ``support_bins`` from ``pairwise_distance_support_bins``).

    Production path for ``homogeneity_score(..., method="entropy")`` and ``evenness_score`` in
    ``metrics_for_notes``; full specification in ``TECHNICAL_MANUAL.md`` §4.4. Single-bin ceiling
    (``k <= 1``) ⇒ **0.0** evenness (fully concentrated).
    """
    if not counts:
        return 0.0
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    k = max(1, int(support_bins))
    if k <= 1:
        return 0.0
    entropy = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            entropy -= p * math.log(p)
    max_h = math.log(k)
    if max_h <= 0.0:
        return 0.0
    return min(1.0, entropy / max_h)


def dominance(counts: Dict[int, int]) -> float:
    if not counts:
        return 0.0
    total = sum(counts.values())
    return max(counts.values()) / total if total > 0 else 0.0


def dominance_weighted(counts: Mapping[int, float]) -> float:
    if not counts:
        return 0.0
    total = sum(counts.values())
    return max(counts.values()) / total if total > 0 else 0.0


def entropy_evenness_supportbounded_weighted(
    counts: Mapping[int, float], support_bins: int
) -> float:
    if not counts:
        return 0.0
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    k = max(1, int(support_bins))
    if k <= 1:
        return 0.0
    entropy = 0.0
    for mass in counts.values():
        p = mass / total
        if p > 0:
            entropy -= p * math.log(p)
    max_h = math.log(k)
    if max_h <= 0.0:
        return 0.0
    return min(1.0, entropy / max_h)


def intervallic_concentration(
    counts: Union[Dict[int, int], Mapping[int, float]],
    method: str,
    support_bins: int,
) -> float:
    """Dominance share or 1 − span-normalized Shannon entropy (concentration)."""
    if not counts:
        return 0.0
    weighted = any(not isinstance(v, int) for v in counts.values())
    if method == "entropy":
        if weighted:
            return 1.0 - entropy_evenness_supportbounded_weighted(counts, support_bins)
        int_counts = {int(k): int(v) for k, v in counts.items()}
        return 1.0 - entropy_evenness_supportbounded(int_counts, support_bins)
    if weighted:
        return dominance_weighted(counts)
    int_counts = {int(k): int(v) for k, v in counts.items()}
    return dominance(int_counts)


def sorted_pitch_units(notes: Sequence[NoteTuple], bin_cents: int = 100) -> list[int]:
    return sorted(
        note_to_units(letter, alter, octave, bin_cents) for letter, alter, octave in notes
    )


def proximity_weighted_distance_counts(
    notes: Sequence[NoteTuple],
    bin_cents: int = 100,
    *,
    inverse_power: int = 1,
) -> Dict[int, float]:
    """
    Weighted histogram of absolute pitch distances for notes sorted by height.

    Pair (i, j) with i < j receives weight 1 / (j - i)^inverse_power.
    """
    units = sorted_pitch_units(notes, bin_cents)
    n = len(units)
    if n < 2:
        return {}
    power = max(1, int(inverse_power))
    weighted: Dict[int, float] = {}
    for i in range(n):
        for j in range(i + 1, n):
            gap = j - i
            d = units[j] - units[i]
            w = 1.0 / float(gap**power)
            weighted[d] = weighted.get(d, 0.0) + w
    return weighted


def resolve_headline_h(
    *,
    pair_score: float,
    chain_score: float,
    weighted_linear_score: float,
    weighted_quadratic_score: float,
    headline_mode: IntervallicHeadlineMode,
    hybrid_alpha: float,
) -> float:
    if headline_mode == IntervallicHeadlineMode.ADJACENT:
        return chain_score
    if headline_mode == IntervallicHeadlineMode.WEIGHTED_LINEAR:
        return weighted_linear_score
    if headline_mode == IntervallicHeadlineMode.WEIGHTED_QUADRATIC:
        return weighted_quadratic_score
    if headline_mode == IntervallicHeadlineMode.HYBRID:
        a = min(1.0, max(0.0, float(hybrid_alpha)))
        return a * chain_score + (1.0 - a) * pair_score
    return pair_score


def dominant_item(counts: Dict[int, int]):
    if not counts:
        return None, 0, 0.0
    total = sum(counts.values())
    k, v = max(counts.items(), key=lambda item: item[1])
    share = v / total if total else 0.0
    return k, v, share


def adjacent_interval_counts_from_notes(notes: Sequence[NoteTuple], bin_cents: int = 100):
    units = sorted(
        note_to_units(letter, alter, octave, bin_cents) for (letter, alter, octave) in notes
    )
    if len(units) < 2:
        return {}, []
    adj = [units[i + 1] - units[i] for i in range(len(units) - 1)]
    counts: Dict[int, int] = {}
    for d in adj:
        counts[d] = counts.get(d, 0) + 1
    return counts, adj


def homogeneity_score(
    notes: Sequence[NoteTuple],
    alpha: float,
    method: str = "dominance",
    bin_cents: int = 100,
    *,
    blend_chain_in_h: bool = False,
    headline_mode: Optional[IntervallicHeadlineMode] = None,
):
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha must be between 0 and 1")
    if method not in {"dominance", "entropy"}:
        raise ValueError("method must be 'dominance' or 'entropy'")

    mode = headline_mode
    if mode is None:
        mode = (
            IntervallicHeadlineMode.HYBRID if blend_chain_in_h else IntervallicHeadlineMode.PAIRWISE
        )

    interval_counts, distance_counts = intervals_for_notes(notes, bin_cents)
    adj_counts, _ = adjacent_interval_counts_from_notes(notes, bin_cents)
    support_bins = pairwise_distance_support_bins(notes, bin_cents)

    chain_score = intervallic_concentration(adj_counts, method, support_bins)
    pair_score = intervallic_concentration(distance_counts, method, support_bins)

    w_lin_counts = proximity_weighted_distance_counts(notes, bin_cents, inverse_power=1)
    w_quad_counts = proximity_weighted_distance_counts(notes, bin_cents, inverse_power=2)
    weighted_linear_score = intervallic_concentration(w_lin_counts, method, support_bins)
    weighted_quadratic_score = intervallic_concentration(w_quad_counts, method, support_bins)

    h = resolve_headline_h(
        pair_score=pair_score,
        chain_score=chain_score,
        weighted_linear_score=weighted_linear_score,
        weighted_quadratic_score=weighted_quadratic_score,
        headline_mode=mode,
        hybrid_alpha=alpha,
    )
    return (
        h,
        chain_score,
        pair_score,
        interval_counts,
        distance_counts,
        adj_counts,
        weighted_linear_score,
        weighted_quadratic_score,
        w_lin_counts,
        w_quad_counts,
    )


def h_band_label(h: float) -> str:
    """
    Categorical band for overall homogeneity H (fixed analytical thresholds; not user-tunable).

    Boundaries: H ≥ 0.80 homogeneous; 0.50 ≤ H < 0.80 moderately homogeneous;
    0.20 ≤ H < 0.50 moderately heterogeneous; H < 0.20 heterogeneous.
    """
    if h >= 0.80:
        return "homogeneous"
    if h >= 0.50:
        return "moderately homogeneous"
    if h >= 0.20:
        return "moderately heterogeneous"
    return "heterogeneous"


def classify_aggregate(
    interval_counts: Dict[str, int],
    dominance_threshold: float,
    even_high: float,
    even_low: float,
    chain_dominance: float = 0.0,
    chain_threshold: float = 0.60,
    *,
    pairwise_abs_evenness: Optional[float] = None,
):
    if not interval_counts:
        return "no intervals"
    total = sum(interval_counts.values())
    top_interval, top_count = max(interval_counts.items(), key=lambda item: item[1])
    dom = top_count / total if total else 0.0
    even = (
        float(pairwise_abs_evenness)
        if pairwise_abs_evenness is not None
        else entropy_evenness(interval_counts)
    )

    dominant_label = (
        f"{top_interval}-dominant" if dom >= dominance_threshold else "no dominant interval"
    )
    if even >= even_high:
        even_label = "high evenness"
    elif even <= even_low:
        even_label = "low evenness"
    else:
        even_label = "mid evenness"
    label = f"{dominant_label}; {even_label}"
    if chain_dominance >= 0.95:
        label += "; uniform stacking"
    elif chain_dominance >= chain_threshold:
        label += "; predominantly regular stacking"
    else:
        label += "; irregular stacking"
    return label
