# Contributing

## Setup

```bash
pip install -e ".[dev]"
```

## Checks (run before a PR or handoff ZIP)

```bash
pytest -q
ruff check iav tests analyze_corpus.py scripts
ruff format --check iav
mypy iav
python analyze_corpus.py --verify-canonical -i examples/corpus -o results_ci
python scripts/validation_report.py tests/fixtures/validation_annotations_minimal.csv --metrics results_ci/results.json --output results_ci/validation
```

## Rules

- Do **not** change intervallic homogeneity **H** formulas or canonical JSON expectations without a demonstrated bug and explicit review.
- **Vertical cardinality** (`iav/vertical_cardinality.py`, §7.8 of the manual) is descriptive only; keep it aligned with **`Notes`** in `slice_summary.csv` and document JSON schema changes in **TECHNICAL_MANUAL.md**. Do **not** infer **`vertical_pitch_class_cardinality`** from unique-pitch count in **`vertical_cardinality_from_summary_row`** — only read explicit **`PC cardinality`** (see `tests/test_vertical_cardinality.py`).
- Keep the **symbolic-only** stance (no perceptual or registral-dispersion claims).
- Preserve root shims: `pitch_model.py`, `analysis_core.py`, `interval_analysis.py`.
- Add regression tests for behaviour changes; prefer invariant / golden tests over random property tests.
- See `docs/VALIDATION_PROTOCOL.md` for human-label studies.

## Release

See `RELEASE_CHECKLIST.md`.
