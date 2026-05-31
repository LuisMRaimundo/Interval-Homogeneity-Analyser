#!/usr/bin/env python3
"""Generate alpha / threshold sensitivity tables for thesis (CSV + Markdown)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iav.analysis_enums import IntervallicHeadlineMode
from iav.canonical_corpus import load_canonical_corpus
from iav.interval_analysis_core import h_band_label, homogeneity_score, metrics_for_notes

OUT_DIR = ROOT / "docs" / "reports"
ALPHAS = [0.3, 0.4, 0.5, 0.6, 0.7]
H_BANDS = [0.80, 0.50, 0.20]


def _write_alpha_sensitivity() -> None:
    _cfg, specs = load_canonical_corpus()
    rows: list[dict] = []
    for sid, spec in specs.items():
        for alpha in ALPHAS:
            h, chain, pair, *_ = homogeneity_score(
                spec.notes,
                alpha=alpha,
                method="dominance",
                bin_cents=100,
                headline_mode=IntervallicHeadlineMode.HYBRID,
            )
            rows.append(
                {
                    "sonority_id": sid,
                    "alpha": alpha,
                    "hybrid_H": round(h, 4),
                    "chain_score": round(chain, 4),
                    "pair_score": round(pair, 4),
                    "H_label_hybrid": h_band_label(h),
                }
            )
    path = OUT_DIR / "sensitivity_alpha.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    md = ["# Sensitivity: hybrid α\n", "| Sonority | α | Hybrid H | Chain | Pair | H band |\n", "|---|---:|---:|---:|---:|---|\n"]
    for r in rows:
        md.append(
            f"| {r['sonority_id']} | {r['alpha']:.1f} | {r['hybrid_H']:.3f} | "
            f"{r['chain_score']:.3f} | {r['pair_score']:.3f} | {r['H_label_hybrid']} |\n"
        )
    (OUT_DIR / "sensitivity_alpha.md").write_text("".join(md), encoding="utf-8")


def _write_threshold_sensitivity() -> None:
    _cfg, specs = load_canonical_corpus()
    rows: list[dict] = []
    for sid, spec in specs.items():
        if sid == "dyad_perfect_fifth":
            continue
        m = metrics_for_notes(
            spec.notes, 0.35, 0.8, 0.3, 0.6, "dominance", bin_cents=100
        )
        h = float(m["H"])
        for cutoff in H_BANDS:
            rows.append(
                {
                    "sonority_id": sid,
                    "headline_H": round(h, 4),
                    "cutoff": cutoff,
                    "above_cutoff": h >= cutoff,
                    "H_label": m["H_label"],
                }
            )
    path = OUT_DIR / "sensitivity_h_bands.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    md = [
        "# Sensitivity: fixed H band cutoffs (0.80 / 0.50 / 0.20)\n\n",
        "Shows which canonical sonorities remain above each cutoff under **pairwise** headline H.\n",
    ]
    (OUT_DIR / "sensitivity_h_bands.md").write_text("".join(md), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_alpha_sensitivity()
    _write_threshold_sensitivity()
    print(f"Wrote reports to {OUT_DIR}")


if __name__ == "__main__":
    main()
