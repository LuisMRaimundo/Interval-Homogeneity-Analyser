"""Batch corpus analysis without Streamlit (CSV/JSON export, reproducible config)."""

from __future__ import annotations

import csv
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from iav.analysis_enums import IntervallicHeadlineMode, MusicXmlImportMode
from iav.canonical_corpus import analyze_sonority, load_canonical_corpus, notes_from_json_rows
from iav.interval_analysis_core import (
    compute_alpha_used,
    dedupe_notes_by_midi,
    metrics_for_notes,
)
from iav.musicxml_io import parse_musicxml_upload
from iav.note_types import NoteTuple

logger = logging.getLogger("iav.batch")


@dataclass
class BatchConfig:
    input_dir: Path
    output_dir: Path
    edo: int = 12
    headline_mode: IntervallicHeadlineMode = IntervallicHeadlineMode.PAIRWISE
    homogeneity_method: str = "dominance"
    hybrid_alpha_base: float = 0.6
    auto_alpha: bool = False
    k_auto: int = 4
    remove_duplicates: bool = True
    apply_sounding_transpose: bool = False
    dominance_threshold: float = 0.35
    even_high: float = 0.8
    even_low: float = 0.3
    chain_threshold: float = 0.60

    @property
    def bin_cents(self) -> int:
        return int(round(1200 / self.edo))


def _load_notes_from_path(path: Path, cfg: BatchConfig) -> List[NoteTuple]:
    if path.suffix.lower() in {".json"}:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw.get("notes", raw)
        return notes_from_json_rows(rows)
    if path.suffix.lower() in {".xml", ".musicxml", ".mxl"}:
        data = path.read_bytes()
        if path.suffix.lower() == ".mxl":
            import zipfile

            with zipfile.ZipFile(path) as zf:
                names = [n for n in zf.namelist() if n.lower().endswith((".xml", ".musicxml"))]
                if not names:
                    raise ValueError(f"No XML inside MXL: {path}")
                data = zf.read(names[0])
        notes, _skipped = parse_musicxml_upload(
            data,
            MusicXmlImportMode.AGGREGATE,
            include_grace=False,
            include_cue=False,
            apply_sounding_transpose=cfg.apply_sounding_transpose,
        )
        return list(notes)
    raise ValueError(f"Unsupported input: {path}")


def _analyze_one(
    source_id: str,
    notes: Sequence[NoteTuple],
    cfg: BatchConfig,
) -> Dict[str, Any]:
    if len(notes) < 2:
        return {"source_id": source_id, "error": "fewer than 2 notes", "note_count": len(notes)}
    work = list(notes)
    if cfg.remove_duplicates:
        work = dedupe_notes_by_midi(work, bin_cents=cfg.bin_cents)
    alpha_used = compute_alpha_used(len(work), cfg.hybrid_alpha_base, cfg.auto_alpha, cfg.k_auto)
    m = metrics_for_notes(
        work,
        cfg.dominance_threshold,
        cfg.even_high,
        cfg.even_low,
        alpha_used,
        cfg.homogeneity_method,
        bin_cents=cfg.bin_cents,
        chain_threshold=cfg.chain_threshold,
        intervallic_headline_mode=cfg.headline_mode,
    )
    canon = analyze_sonority(
        work,
        hybrid_alpha=alpha_used,
        homogeneity_method=cfg.homogeneity_method,
        bin_cents=cfg.bin_cents,
        dominance_threshold=cfg.dominance_threshold,
        even_high=cfg.even_high,
        even_low=cfg.even_low,
        chain_threshold=cfg.chain_threshold,
    )
    row: Dict[str, Any] = {
        "source_id": source_id,
        "note_count": len(work),
        "headline_H": round(float(m["H"]), 6),
        "H_label": m["H_label"],
        "classification": m["classification"],
        "headline_mode": cfg.headline_mode.value,
        "alpha_used": round(alpha_used, 6),
        **{k: canon[k] for k in canon},
    }
    return row


def discover_inputs(input_dir: Path) -> List[Path]:
    patterns = ("*.json", "*.xml", "*.musicxml", "*.mxl")
    files: List[Path] = []
    for pat in patterns:
        files.extend(sorted(input_dir.glob(pat)))
    return files


def run_batch(cfg: BatchConfig) -> Dict[str, Any]:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = cfg.output_dir / "log.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    config_used = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **{
            k: (
                v.value
                if isinstance(v, IntervallicHeadlineMode)
                else str(v)
                if isinstance(v, Path)
                else v
            )
            for k, v in asdict(cfg).items()
        },
    }
    (cfg.output_dir / "config_used.json").write_text(
        json.dumps(config_used, indent=2), encoding="utf-8"
    )

    rows: List[Dict[str, Any]] = []
    for path in discover_inputs(cfg.input_dir):
        logger.info("Analyzing %s", path.name)
        try:
            notes = _load_notes_from_path(path, cfg)
            rows.append(_analyze_one(path.stem, notes, cfg))
        except Exception as exc:
            logger.exception("Failed %s", path)
            rows.append({"source_id": path.stem, "error": str(exc)})

    results_json = {"config": config_used, "results": rows}
    (cfg.output_dir / "results.json").write_text(
        json.dumps(results_json, indent=2), encoding="utf-8"
    )

    if rows:
        fieldnames: List[str] = []
        for r in rows:
            for k in r:
                if k not in fieldnames:
                    fieldnames.append(k)
        with (cfg.output_dir / "results.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    numeric_keys = [
        "pair_score",
        "chain_score",
        "weighted_linear_score",
        "weighted_quadratic_score",
        "hybrid_score",
        "headline_H",
    ]
    summary: Dict[str, Any] = {"count": len(rows), "means": {}}
    for key in numeric_keys:
        vals = [float(r[key]) for r in rows if key in r and r.get("error") is None]
        if vals:
            summary["means"][key] = round(sum(vals) / len(vals), 6)
    (cfg.output_dir / "summary_statistics.csv").write_text(
        "metric,mean\n" + "\n".join(f"{k},{v}" for k, v in summary["means"].items()) + "\n",
        encoding="utf-8",
    )
    logger.info("Wrote %d rows to %s", len(rows), cfg.output_dir)
    return results_json


def run_canonical_verification(output_dir: Optional[Path] = None) -> int:
    """Verify bundled canonical corpus; optional copy report to output_dir."""
    cfg, specs = load_canonical_corpus()
    from iav.canonical_corpus import verify_sonority_metrics

    failures: List[str] = []
    report_rows: List[Dict[str, Any]] = []
    for sid, spec in specs.items():
        computed = analyze_sonority(
            spec.notes,
            hybrid_alpha=cfg.hybrid_alpha,
            homogeneity_method=cfg.homogeneity_method,
            bin_cents=cfg.bin_cents,
        )
        try:
            verify_sonority_metrics(computed, spec.expected, sid)
            ok = True
        except AssertionError as exc:
            ok = False
            failures.append(str(exc))
        report_rows.append({"sonority_id": sid, "ok": ok, **computed})

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "canonical_verification.json").write_text(
            json.dumps({"failures": failures, "results": report_rows}, indent=2),
            encoding="utf-8",
        )
    if failures:
        for f in failures:
            logger.error(f)
        return 1
    return 0
