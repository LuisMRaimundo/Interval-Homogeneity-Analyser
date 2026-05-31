"""Display formatting for aggregate results (no Streamlit)."""

from __future__ import annotations

from typing import Any, Mapping, Optional


def interval_heterogeneity(homogeneity: Optional[float]) -> Optional[float]:
    """Symbolic complement 1 − H when H is defined."""
    if homogeneity is None:
        return None
    return 1.0 - float(homogeneity)


def headline_summary_line(metrics: Mapping[str, Any]) -> str:
    """One-line textual summary of headline H and band label."""
    h = metrics.get("H")
    label = metrics.get("H_label", "")
    title = metrics.get("H_primary_title", "Homogeneity (H)")
    if h is None:
        return f"{title}: —"
    het = interval_heterogeneity(float(h))
    het_s = f"{het:.3f}" if het is not None else "—"
    return f"{title}: **{float(h):.3f}** ({label}) · Interval heterogeneity (1−H): **{het_s}**"


def classification_display(classification: str) -> str:
    return str(classification or "").strip() or "(no classification)"
