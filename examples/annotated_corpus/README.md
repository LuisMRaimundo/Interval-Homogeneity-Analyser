# Annotated corpus (pilot study)

Human **labels** in `manifest.json` are compared against computed intervallic metrics (`iav/annotated_study.py`). This is a **pilot** scaffold for thesis-style agreement tables—not a validated psychometric benchmark.

Run from the repository root:

```bash
python scripts/run_annotated_study.py
```

Outputs land under `docs/reports/annotated_pilot/` (CSV + short summary). Extend `manifest.json` with new sonority IDs pointing at note lists or corpus JSON paths.

See [TECHNICAL_MANUAL.md](../../TECHNICAL_MANUAL.md) §10.5 and [README.md](../../README.md).
