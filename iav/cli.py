"""Command-line entry: iav-analyze / analyze_corpus.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from iav.analysis_enums import intervallic_headline_mode_from_str
from iav.batch_analyze import BatchConfig, run_batch, run_canonical_verification


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="iav-analyze",
        description="Batch intervallic analysis (no Streamlit).",
    )
    p.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Folder with .json note lists and/or MusicXML files",
    )
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Output folder (results.csv, results.json, config_used.json, log.txt)",
    )
    p.add_argument("--edo", type=int, default=12, choices=[12, 24, 48])
    p.add_argument(
        "--headline",
        default="pairwise_intervallic_concentration",
        help="IntervallicHeadlineMode value",
    )
    p.add_argument(
        "--method",
        default="dominance",
        choices=["dominance", "entropy", "combined"],
    )
    p.add_argument("--alpha", type=float, default=0.6, help="Hybrid α (adjacent weight)")
    p.add_argument("--auto-alpha", action="store_true")
    p.add_argument("--k-auto", type=int, default=4)
    p.add_argument("--no-dedupe", action="store_true")
    p.add_argument(
        "--sounding-transpose",
        action="store_true",
        help="Apply MusicXML <transpose> when reading .xml/.mxl (concert pitch)",
    )
    p.add_argument(
        "--verify-canonical",
        action="store_true",
        help="Run bundled canonical sonority regression and write canonical_verification.json",
    )
    p.add_argument(
        "--export",
        default="csv,json",
        help="Comma-separated: csv, json (always written when batch runs)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.verify_canonical:
        code = run_canonical_verification(args.output)
        if code != 0:
            return code
        if not args.input.exists():
            return 0

    if not args.input.is_dir():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 2

    cfg = BatchConfig(
        input_dir=args.input,
        output_dir=args.output,
        edo=args.edo,
        headline_mode=intervallic_headline_mode_from_str(args.headline),
        homogeneity_method=args.method,
        hybrid_alpha_base=args.alpha,
        auto_alpha=args.auto_alpha,
        k_auto=args.k_auto,
        remove_duplicates=not args.no_dedupe,
        apply_sounding_transpose=args.sounding_transpose,
    )
    run_batch(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
