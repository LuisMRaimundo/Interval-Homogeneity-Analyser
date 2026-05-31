# Release checklist

1. `pytest -q` — all green.
2. `ruff check iav tests analyze_corpus.py scripts` and `ruff format --check iav`.
3. `mypy iav`.
4. `python analyze_corpus.py --verify-canonical -i examples/corpus -o results_verify`.
5. `python scripts/sensitivity_report.py` (optional thesis tables).
6. `python scripts/run_annotated_study.py` (if annotated corpus unchanged).
7. `pwsh -File scripts/make_release_zip.ps1` then `pwsh -File scripts/verify_release_zip.ps1 -ZipPath <zip>`.
8. Confirm `TECHNICAL_MANUAL.md` version line and §7.6–7.8 if passage exports or vertical cardinality behaviour changed (including JSON PC-cardinality rules and chart vs JSON scope).
9. After editing Python under `iav/`, run `ruff format iav tests` so repository files stay normally formatted (not single-line minified blobs).
9. Do **not** regenerate `iav/data/canonical_*.json` unless fixing a verified regression.

## Version bump

Update `version` in `pyproject.toml` and document history in `TECHNICAL_MANUAL.md` § Document history.
