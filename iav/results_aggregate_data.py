"""Pure helpers to build interval-count rows and the analysis CSV (no Streamlit)."""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional

from iav.analysis_enums import HomogeneityMethod
from iav.interval_analysis_core import units_to_label
from iav.widget_state import WidgetState


def semi_distance_rows(
    distance_counts: Dict[int, int], total_intervals: int, bin_cents: int
) -> List[Dict[str, Any]]:
    return [
        {
            "Cents": k * bin_cents,
            "Label": units_to_label(k, bin_cents),
            "Count": v,
            "Percent": round(100 * v / total_intervals, 2),
        }
        for k, v in sorted(distance_counts.items(), key=lambda item: (item[0]))
    ]


def adjacency_rows(
    adj_counts: Dict[int, int], note_count: int, bin_cents: int
) -> List[Dict[str, Any]]:
    adj_total = max(1, note_count - 1)
    return [
        {
            "Cents": k * bin_cents,
            "Label": units_to_label(k, bin_cents),
            "Count": v,
            "Percent": round(100 * v / adj_total, 2),
        }
        for k, v in sorted(adj_counts.items(), key=lambda item: (item[0]))
    ]


def interval_label_rows(
    interval_counts: Dict[str, int], total_intervals: int
) -> List[Dict[str, Any]]:
    return [
        {"Interval": k, "Count": v, "Percent": round(100 * v / total_intervals, 2)}
        for k, v in sorted(interval_counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def write_analysis_csv(
    writer: Any,
    w: WidgetState,
    note_count: int,
    total_intervals: int,
    metrics: Dict[str, Any],
    alpha_used: float,
    h_main: float,
    semi_rows: List[Dict[str, Any]],
    adj_rows: List[Dict[str, Any]],
    interval_rows: List[Dict[str, Any]],
    pc_set_summary: Optional[Dict[str, Any]],
) -> None:
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total notes", note_count])
    writer.writerow(["Total pairwise intervals", total_intervals])
    if w.homogeneity_method == HomogeneityMethod.COMBINED:
        writer.writerow(["Homogeneity (dominance)", f"{metrics['H_dom']:.6f}"])
        writer.writerow(["Homogeneity (entropy)", f"{metrics['H_ent']:.6f}"])
        writer.writerow(["Homogeneity (consensus)", f"{metrics['H_consensus']:.6f}"])
        writer.writerow(["Heterogeneity (consensus)", f"{(1.0 - metrics['H_consensus']):.6f}"])
    else:
        writer.writerow([metrics.get("H_primary_title", "Homogeneity (H)"), f"{h_main:.6f}"])
        writer.writerow(["Heterogeneity (1 − H)", f"{(1.0 - h_main):.6f}"])
    writer.writerow(["Headline intervallic metric", w.intervallic_headline_mode.value])
    writer.writerow(
        [
            "Pairwise entropy support bins (span+1)",
            str(metrics.get("pairwise_entropy_support_bins", "")),
        ]
    )
    writer.writerow(["Alpha base (chain weight)", f"{w.alpha_base:.2f}"])
    writer.writerow(["Alpha used (after auto-adjust)", f"{alpha_used:.6f}"])
    writer.writerow(["Auto-adjust alpha", str(w.auto_alpha)])
    writer.writerow(["Auto-adjust k", str(w.k_auto)])
    if w.homogeneity_method == HomogeneityMethod.COMBINED:
        writer.writerow(["Chain dominance", f"{metrics['chain_dom']:.6f}"])
        writer.writerow(["Pairwise dominance", f"{metrics['pair_dom']:.6f}"])
        writer.writerow(["Chain concentration", f"{metrics['chain_ent']:.6f}"])
        writer.writerow(["Pairwise concentration", f"{metrics['pair_ent']:.6f}"])
    else:
        writer.writerow(
            [
                metrics.get("chain_metric_title", f"Chain {w.score_label}"),
                f"{metrics['chain_score']:.6f}",
            ]
        )
        writer.writerow(
            [
                metrics.get("pair_metric_title", f"Pairwise {w.score_label}"),
                f"{metrics['pair_score']:.6f}",
            ]
        )
        if metrics.get("weighted_linear_score") is not None:
            writer.writerow(
                [
                    metrics.get("weighted_linear_metric_title", "Proximity-weighted linear"),
                    f"{metrics['weighted_linear_score']:.6f}",
                ]
            )
        if metrics.get("weighted_quadratic_score") is not None:
            writer.writerow(
                [
                    metrics.get("weighted_quadratic_metric_title", "Proximity-weighted quadratic"),
                    f"{metrics['weighted_quadratic_score']:.6f}",
                ]
            )
    writer.writerow(["Dominant adjacent interval", metrics.get("top_chain_label") or ""])
    writer.writerow(["Dominant adjacent share", f"{metrics.get('top_chain_semi_share', 0.0):.6f}"])
    writer.writerow(["Dominant pairwise interval", metrics.get("top_pair_label") or ""])
    writer.writerow(["Dominant pairwise share", f"{metrics.get('top_pair_semi_share', 0.0):.6f}"])
    writer.writerow(
        [
            metrics.get("evenness_title", "Evenness (entropy, pairwise)"),
            f"{metrics['evenness_score']:.6f}",
        ]
    )
    writer.writerow(["Type concentration (pairwise, custom)", f"{metrics['type_score']:.6f}"])
    writer.writerow(["Aggregate label (pairwise + chain)", metrics["classification"]])
    writer.writerow(["H classification", metrics["H_label"]])
    writer.writerow(["Pitch span (cents)", metrics["pitch_span"]])
    writer.writerow(["Avg pairwise distance", f"{metrics['avg_distance']:.6f}"])
    writer.writerow(["Cluster compactness", f"{metrics['compactness_score']:.6f}"])
    if pc_set_summary is not None:
        writer.writerow(
            ["Pitch classes sorted (12-TET)", str(pc_set_summary["pitch_classes_sorted"])]
        )
        writer.writerow(["Normal order (12-TET)", pc_set_summary["normal_order_str"]])
        writer.writerow(["Prime form (12-TET)", pc_set_summary["prime_form_str"]])
        writer.writerow(["Interval vector ic1–ic6", pc_set_summary["interval_vector_str"]])
    writer.writerow([])
    writer.writerow(["Pairwise cents", "Label", "Count", "Percent"])
    for row in semi_rows:
        writer.writerow([row["Cents"], row["Label"], row["Count"], row["Percent"]])
    writer.writerow([])
    writer.writerow(["Adjacent cents", "Label", "Count", "Percent"])
    for row in adj_rows:
        writer.writerow([row["Cents"], row["Label"], row["Count"], row["Percent"]])
    writer.writerow([])
    writer.writerow(["Pairwise interval label", "Count", "Percent"])
    for row in interval_rows:
        writer.writerow([row["Interval"], row["Count"], row["Percent"]])


def analysis_csv_string(
    w: WidgetState,
    note_count: int,
    total_intervals: int,
    metrics: Dict[str, Any],
    alpha_used: float,
    h_main: float,
    semi_rows: List[Dict[str, Any]],
    adj_rows: List[Dict[str, Any]],
    interval_rows: List[Dict[str, Any]],
    pc_set_summary: Optional[Dict[str, Any]],
) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    write_analysis_csv(
        writer,
        w,
        note_count,
        total_intervals,
        metrics,
        alpha_used,
        h_main,
        semi_rows,
        adj_rows,
        interval_rows,
        pc_set_summary,
    )
    return buf.getvalue()
