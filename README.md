# Intervallic_Homogeneity

**Repository:** [github.com/LuisMRaimundo/Intervallic_Homogeneity](https://github.com/LuisMRaimundo/Intervallic_Homogeneity)

Streamlit app for **intervallic homogeneity** in notated pitch aggregates (non-octave-equivalent intervals), from manual note entry or MusicXML — including **H-over-time** passage profiles and **vertical symbolic cardinality** (note-count thickness per slice) for verticality slices.

**Semantic scope:** symbolic / score-based interval descriptors — not audio, spectral, or psychoacoustic consonance analysis. See [docs/METRIC_SEMANTICS.md](docs/METRIC_SEMANTICS.md).

## Setup

From this directory, install the package in editable mode so the **`iav`** package and root **shims** (`pitch_model`, `analysis_core`, `interval_analysis`) resolve:

```bash
pip install -e ".[dev]"
```

`[dev]` adds **pytest**, **ruff**, and **mypy**. To run the app only: `pip install -e .`

## Run

### No Python installed? (one-click)

See **[installers/README.md](installers/README.md)**:

| Platform | Launcher |
|----------|----------|
| **Windows 10/11** | Double-click `installers\windows\Install and Run.bat` |
| **macOS** | Double-click `installers/macos/Install and Run.command` (after `chmod +x`) |
| **Linux** | `./installers/linux/install-and-run.sh` |

First run downloads a private Python and libraries; the browser opens at **http://localhost:8501**.

### Developers (Python already installed)

```bash
pip install -e .
streamlit run app.py
```

Use the sidebar page **Which metric to use?** to choose headline **H** (pairwise vs adjacent vs weighted vs hybrid).

### Default analysis model (presets)

Open **Analysis presets** on the main page and choose **①–④**, then **Apply preset now** (or enable auto-apply). Defaults match [ANALYSIS_PRESET.md](ANALYSIS_PRESET.md):

| Setting | Default |
|---------|---------|
| Headline **H** | **Pairwise intervallic concentration** |
| Homogeneity scoring | **Dominance (max share)** |
| Thresholds | **Fixed (heuristic)** |
| Pitches | **Collapse to unique** on the selected EDO grid |
| MusicXML transpose | **Off** (written pitch); enable **Apply MusicXML transposition (concert pitch)** when needed |

For **MusicXML passages** (many chords over time): use **Verticalities** or **Sounding verticalities** with **All slices** or **Time window** — not **Aggregate** (which pools all pitches into one sonority). The app shows an **H-over-time chart**, a **vertical note-count chart**, **`slice_summary.csv`**, and **`vertical_cardinality_profile.json`** (see [TECHNICAL_MANUAL.md §7.6–7.8](TECHNICAL_MANUAL.md)).

## Batch analysis (no Streamlit)

```bash
python analyze_corpus.py --input examples/corpus --output results/
python analyze_corpus.py --verify-canonical -i examples/corpus -o results/
python analyze_corpus.py -i examples/corpus -o results/ --sounding-transpose
```

After `pip install -e .`, the same entry point is available as **`iav-analyze`**.

Outputs: `results.csv`, `results.json`, `config_used.json`, `log.txt`, `summary_statistics.csv`.

Canonical regression: **`iav/data/canonical_sonorities.json`** (13 sonorities) and **`iav/data/canonical_musicxml.json`** (5 MusicXML scores) — see `tests/test_canonical_sonorities.py`, `tests/test_canonical_musicxml.py`. Regenerate with `python scripts/generate_canonical_expectations.py` and `python scripts/build_canonical_musicxml.py`.

Sensitivity tables for thesis: `python scripts/sensitivity_report.py` → `docs/reports/` (generated files are gitignored; see `docs/reports/README.md`). Notebook: `notebooks/sensitivity_report.ipynb`.

Annotated pilot (human labels): `python scripts/run_annotated_study.py` → `docs/reports/annotated_pilot/`.

## Documentation

- **Metric meaning and interpretive limits (H, pair_score, adjacent, EDO, MusicXML):** [docs/METRIC_SEMANTICS.md](docs/METRIC_SEMANTICS.md)
- **Contributing / CI:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Validation protocol (human labels):** [docs/VALIDATION_PROTOCOL.md](docs/VALIDATION_PROTOCOL.md)
- **Fixed analysis preset (exact UI labels):** [ANALYSIS_PRESET.md](ANALYSIS_PRESET.md)
- **Interface quick guide (non-specialists):** [QUICK_GUIDE.md](QUICK_GUIDE.md)
- **Code layout / hygiene before zipping:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Full specification (math, algorithms, MusicXML, tutorial):** [TECHNICAL_MANUAL.md](TECHNICAL_MANUAL.md)
- **MusicXML scope / limitations:** [docs/MUSICXML_COVERAGE.md](docs/MUSICXML_COVERAGE.md)

## Tests

Install **runtime dependencies** (see `pyproject.toml` `[project] dependencies`) plus **pytest** — e.g. `pip install -e ".[dev]"` for everything including **ruff** and **mypy**, or `pip install pytest` plus the runtime list if you only want tests.

Run **`pytest`** from this directory (the repository root). **`pythonpath = ["."]`** is set in `pyproject.toml` so collection resolves **`iav`** and the root **shims** (`pitch_model`, `analysis_core`, `interval_analysis`) **without** requiring `pip install -e .` first — useful for an unpacked ZIP. An **editable install** is still recommended for day-to-day work so tools and imports match an installed layout. Typical full suite: **574** tests (`pytest tests -q`).

Implementations live under **`iav/`**; legacy tests may still `import pitch_model` / `analysis_core` / `interval_analysis` — those modules are thin **shims** (`tests/test_backward_compat_shims.py` locks shim ↔ package identity). The chart smoke module (`tests/test_charts_smoke.py`) imports **`altair`** and **`pandas`**: if those are not installed, those tests are **skipped** automatically.

## Continuous integration

On GitHub, **Actions** runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml) on **push** / **pull request**: **`pytest`**, **`ruff check`**, **`ruff format --check`**, **`mypy`** on `iav`, canonical sonority + MusicXML verification, batch smoke on `examples/corpus/`, sensitivity report, annotated pilot, and optional **music21** interval-vector comparison (Python 3.10–3.11).

## Lint and static typing (optional)

With `[dev]` installed:

```bash
ruff check iav
ruff format iav
mypy
```

(`ci.yml` uses **`ruff format --check iav`**; omit `--check` locally to apply formatting.)

`mypy` is configured for the **`iav`** package at a pragmatic strictness level (see `pyproject.toml`).

### Repository hygiene before a ZIP

- **Critical:** compressing the project folder with Explorer, Finder, or “select all → ZIP” **will ship `.venv` (~hundreds of MB), `.pytest_cache`, `.ruff_cache`, `__pycache__`, and `*.egg-info`** unless you removed them first. Reviewers treat that as poor release discipline. The **only** supported handoff path is the script below (which also runs **`verify_release_zip`** on the produced archive).
- **Recommended (controlled deliverable):** run **`pwsh -File scripts/make_release_zip.ps1`** (Windows) or **`sh scripts/make_release_zip.sh`** (macOS/Linux). This runs the clean step, then writes a **source-only** `.zip` next to the project folder (timestamped name), explicitly **excluding** `.venv`, caches, `.git`, `build/`, `dist/`, `__pycache__`, `*.egg-info`, and similar. Your local venv is left in place; it is simply omitted from the archive. The script ends with **`verify_release_zip`**: if that step does not print “ZIP verification OK”, **do not submit** the file. Optional path: `pwsh -File scripts/make_release_zip.ps1 -OutZip "D:\exports\ia.zip"`.
- **POSIX / line endings:** `scripts/*.sh` are **LF-only** (enforced via `.gitattributes`). If `sh scripts/make_release_zip.sh` fails with errors like `$'\r': command not found`, the checkout has CRLF in those files; use the **PowerShell** release script on Windows, or re-clone with `core.autocrlf=false` / `git add --renormalize` after pulling this fix.
- **Clean only:** **`pwsh -File scripts/clean_repo.ps1`** or **`sh scripts/clean_repo.sh`** (see `docs/ARCHITECTURE.md`) strips `__pycache__`, pytest/mypy/ruff caches, `build/` / `dist/`, `*.egg-info`, coverage junk, and stray `*.docx` / `*.mhtml`. **`.venv/` is not removed** unless you pass **`-IncludeVenv`** / **`--include-venv`** (destructive: you must recreate the env).

## Notes

- **Downstream package use:** [Timbral_Instrumental_Homogeneity](https://github.com/LuisMRaimundo/Timbral_Instrumental_Homogeneity) imports **`iav.vertical_cardinality`** for symbolic vertical note-count metrics in score analysis. Install this repository (editable or `pip install git+https://github.com/LuisMRaimundo/Intervallic_Homogeneity.git`) where that dependency is required.
- Manual input uses a single **Note** column: `C4`, `D#3`, `Eb`, `F##` (octave defaults to 4 if omitted).
- MusicXML upload accepts `.xml`, `.musicxml`, or `.mxl` (compressed).
- MusicXML import supports **aggregate** (single sonority), **onset verticalities**, or **sounding verticalities**. Passage analysis: verticality modes + slice summary table + **homogeneity timeline chart** + **vertical cardinality chart** + JSON export (§7.6–7.8 of the manual). Manual/aggregate mode also exports **`vertical_cardinality_profile.json`** (single time point). Aggregate on long scores triggers a warning when note count > 50.
- **Vertical cardinality** counts symbolic notes per vertical slice (not acoustic density or registral dispersion); see §7.8 of the manual. The passage chart plots **note count** only; JSON may include unique-pitch and pitch-class fields when computed — pitch-class values are **never** inferred from unique-pitch count when the CSV column is absent.
- Interval labels follow the selected EDO grid (e.g., `P4`, `m3`, `TT4` in 12-EDO, or `150c` in microtonal grids); enharmonic spellings are not distinguished.
- This is symbolic pitch-distance analysis; it does not model acoustics (spectra/roughness/critical bands).
- MusicXML timing is normalized to quarter-note units using `<divisions>`.
- EDO selection (12/24/48) controls pitch quantization and interval labels (cents for microtonal grids).
- MusicXML: default is **written** `<pitch>`. In the app, enable **Apply MusicXML transposition (concert pitch)**; in batch CLI use **`--sounding-transpose`**. Low-level APIs: **`parse_musicxml_upload`** or `*_with_sounding_transpose` — see `TECHNICAL_MANUAL.md` §7.1.
- Homogeneity (dominance / entropy concentration / consensus) and related labels are **custom exploratory heuristics**; they are **not** externally validated standard post-tonal measures (see `TECHNICAL_MANUAL.md` §4–5).
- **Pitch-class / Forte-style tools** (§6 of the manual) apply only when every note maps to an integral 12-TET step; they are **orthogonal** to the spelling printed in a score.
- Validation fixtures are in `validation/fixtures/`; additional stress patterns for regression are in `validation/corpus/` (see that folder’s README). Run `pytest` after install as above.

## Copyright and use

Copyright © 2026 Luís Raimundo. All rights reserved.

This repository and its contents are proprietary research material. **No open-source licence is granted.** No permission to copy, redistribute, modify, publish, or derive works without prior written permission from the copyright holder.

**Contact:** lmr.2020@outlook.pt

## Acknowledgements

Developed with support from **FCT** and **Universidade NOVA de Lisboa** (DOI: [10.54499/2020.08817.BD](https://doi.org/10.54499/2020.08817.BD)). The author thanks **Isabel Pires** for her support.
