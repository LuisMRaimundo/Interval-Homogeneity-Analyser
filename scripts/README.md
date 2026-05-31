# Scripts

Run from the **repository root** (the folder that contains `app.py` and `pyproject.toml`).

| Script | Purpose |
|--------|---------|
| `clean_repo.ps1` / `clean_repo.sh` | Remove caches, `build/` / `dist/`, `*.egg-info`, generated `docs/reports/*` (keeps `docs/reports/README.md`). |
| `generate_canonical_expectations.py` | Regenerate `iav/data/canonical_sonorities.json`. |
| `build_canonical_musicxml.py` | Regenerate `validation/canonical/*.xml` and `iav/data/canonical_musicxml.json`. |
| `sensitivity_report.py` | Thesis sensitivity tables → `docs/reports/` (gitignored output). |
| `run_annotated_study.py` | Human-label pilot → `docs/reports/annotated_pilot/`. |

**Not in this folder:** analysis presets and UI copy live in **`iav/analysis_presets.py`** and **[ANALYSIS_PRESET.md](../ANALYSIS_PRESET.md)**.
| `make_release_zip.ps1` / `.sh` | Source-only ZIP for handoff (runs clean + verify). |
| `verify_release_zip.ps1` / `.sh` | Fail if a ZIP contains `.venv`, caches, etc. |

Batch analysis without Streamlit: `python analyze_corpus.py` or `iav-analyze` (see root `README.md`). Add `--sounding-transpose` for concert-pitch MusicXML.
