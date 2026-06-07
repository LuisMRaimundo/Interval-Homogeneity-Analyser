# Architecture — Interval Aggregate Analyzer

## Package layout (canonical)

| Module / package | Role |
|------------------|------|
| **`iav.pitch_model`** | 12-TET MIDI floats, MusicXML accidental token table, respelling after transpose. |
| **`iav.musicxml_io`** (package) | Secure XML/MXL reading and temporal parsers. Submodules: **`_xml_primitives`** (pitch / tie / transpose helpers), **`_flat_score`** (container + flat note list), **`_measure_voice_cursor`** (shared measure timeline), **`_onset_verticalities`**, **`_sounding_verticalities`**. Public API is re-exported from **`iav.musicxml_io`** (`__init__.py`). |
| **`iav.interval_analysis_core`** (package) | Pairwise intervals, homogeneity heuristics, manual table parsing, aggregate metrics, re-exports set-class helpers. Submodules: **`_edo_labels`**, **`_homogeneity`**, **`_manual_input`**, **`_metrics_for_notes`**. Public API is re-exported from **`iav.interval_analysis_core`** (`__init__.py`). |
| **`iav.set_class_12tet`** | Forte-style pitch-class set tools (prime form, interval vector, normal order). |
| **`iav.symbolic_profile`** | Optional intervallic supplements: mod-12 ic evenness, reference interval fingerprints (`iav/data/reference_sonorities.json`). Not registral dispersion. |
| **`iav.vertical_cardinality`** | Symbolic vertical thickness per slice: **`vertical_cardinality_for_notes`**, **`enrich_slice_summary_row`**, **`vertical_cardinality_from_summary_row`** (PC only from explicit CSV column), **`build_vertical_cardinality_profile`**. Not acoustic density. |
| **`iav.analysis_enums`**, **`iav.analysis_presets`**, **`iav.aggregate_metrics`**, **`iav.widget_state`** | Enumerated UI/analysis modes; preset ①–④ session values (**`ANALYSIS_PRESET.md`**); structured `AggregateHomogeneityMetrics`; frozen `WidgetState`. |
| **`iav.note_types`** | `NoteTuple` alias and optional **`SpelledPitch`** dataclass. |
| **`iav.musicxml`**, **`iav.widgets`**, **`iav.results`**, **`iav.charts`** | Streamlit-facing orchestration, CSV/JSON export, Altair charts. **`charts`:** pairwise/adjacent bars, register plot, **`chart_homogeneity_over_time`**, **`chart_vertical_cardinality_over_time`**. **`musicxml`:** slice summary + both timeline charts + `slice_summary.csv` + `vertical_cardinality_profile.json`. **`results`:** aggregate export including cardinality JSON. |
| **`iav.note_sources`** | Merge manual + MusicXML note lists (no Streamlit). |
| **`iav.canonical_corpus`**, **`iav.canonical_musicxml`** | Load frozen regression expectations (`iav/data/*.json`). |
| **`iav.batch_analyze`**, **`iav/cli`**, **`analyze_corpus.py`** | Headless corpus runs and `iav-analyze` entry point. |
| **`iav.annotated_study`** | Compare metrics to human labels in `examples/annotated_corpus/`. |
| **`iav.metric_guide_content`** | Text for sidebar page **Which metric to use?** |
| **`pages/1_Which_metric_to_use.py`** | Streamlit multipage metric decision guide. |
| **`app.py`**, **`interval_analyzer_ui.py`** | Streamlit entry and thin UI shell. |
| **`scripts/`** | Index: `scripts/README.md`. Maintenance: `clean_repo.*`. Data: `generate_canonical_expectations.py`, `build_canonical_musicxml.py`, `sensitivity_report.py`, `run_annotated_study.py`. Release: `make_release_zip.*`, `verify_release_zip.*`. |
| **`installers/`** | One-click launchers (Windows `.bat`, macOS `.command`, Linux `.sh`) + `common/bootstrap.py`; private runtime under `installers/runtime/` (gitignored). See **`installers/README.md`**. |
| **`validation/canonical/`** | Minimal MusicXML scores for canonical_musicxml regression. |

## Backward-compatible shims (repository root)

Legacy imports used in notebooks, tests, and older scripts are preserved:

- `pitch_model.py` → re-exports **`iav.pitch_model`**
- `analysis_core.py` → re-exports **`iav.musicxml_io`**
- `interval_analysis.py` → re-exports **`iav.interval_analysis_core`** (including set-class symbols)

**New code** should import from `iav.*` directly.

## Scientific scope (where logic lives)

**Metric semantics (interpretive):** [METRIC_SEMANTICS.md](METRIC_SEMANTICS.md) — what **H**, **pair_score**, **chain_score**, dominance, entropy, EDO, and MusicXML modes measure and do *not* measure.

- **Pitch distance vs spelling:** interval sizes and homogeneity use quantized height from `chromatic_midi_float` / `note_to_units`. Pairwise **labels** are grid summaries, not voice-leading–aware spellings.
- **Octave:** default pairwise analysis is **not** octave-equivalent unless you interpret §6 pitch-class tools in the technical manual.
- **Homogeneity (H, bands, “combined”):** implemented under **`iav.interval_analysis_core`**. Four intervallic concentrations (pairwise, adjacent, proximity-weighted linear/quadratic) are always computed; headline **H** selects one via **`IntervallicHeadlineMode`** (default pairwise). Hybrid: `H = α·adjacent + (1−α)·pairwise`. See **`TECHNICAL_MANUAL.md`** §4.5.
- **MusicXML `<transpose>`:** Default is **written** `<pitch>`. The Streamlit checkbox **Apply MusicXML transposition (concert pitch)** and CLI **`--sounding-transpose`** route through **`parse_musicxml_upload`** (see `iav/musicxml_io/_dispatch.py`). Low-level `*_with_sounding_transpose` APIs remain for tests and scripts.

## Tests and imports

**`[tool.pytest.ini_options]`** in **`pyproject.toml`** sets **`pythonpath = ["."]`**, so **`pytest`** run from the repository root puts the project root on `sys.path`. That lets **`import iav`** and **`import interval_analysis`** (root shims) resolve **without** setting **`PYTHONPATH=.`** in the shell and **without** requiring **`pip install -e .`** for test collection and execution (useful for an unpacked tree).

An **editable install** (`pip install -e ".[dev]"`) is still recommended for day-to-day development so tooling, metadata, and “installed package” behaviour stay aligned.

Core tests exercise **`iav.musicxml_io`** and **`iav.interval_analysis_core`** indirectly through the shims (`tests/test_backward_compat_shims.py` asserts shim ↔ package identity).

## Before archiving or sharing a ZIP

**Do not** ship a folder compressed with Explorer / Finder alone: it will include **`.venv`**, caches, and build junk. Use the scripted pipeline (runs **`clean_repo`**, **`tar`** with excludes, then **`verify_release_zip`**). If **`verify_release_zip`** does not report success, the archive is **not** a valid handoff.

**`scripts/*.sh`** are **LF-only** (see **`.gitattributes`**). CRLF in those files breaks **`sh scripts/...`** on macOS/Linux (including cryptic `$'\r': command not found`). On Windows, prefer **`pwsh -File scripts/make_release_zip.ps1`** if the shell scripts fail for that reason.

```powershell
pwsh -File scripts/make_release_zip.ps1
```

```sh
sh scripts/make_release_zip.sh
```

To **audit** an existing archive (fails if listing contains venv, caches, `*.egg-info`, or `__pycache__`):

```powershell
pwsh -File scripts/verify_release_zip.ps1 -ZipPath "C:\path\to\archive.zip"
```

```sh
sh scripts/verify_release_zip.sh /path/to/archive.zip
```

The ZIP is written next to the repository folder by default (timestamped `*-source-*.zip`). Override the path with `pwsh -File scripts/make_release_zip.ps1 -OutZip "C:\path\to\out.zip"` or `sh scripts/make_release_zip.sh /path/to/out.zip`.

**Clean working tree only** (before manual zipping or commits):

```powershell
pwsh -File scripts/clean_repo.ps1
```

```sh
sh scripts/clean_repo.sh
```

This removes `__pycache__`, pytest/mypy/ruff caches, `build/`, `dist/`, `*.egg-info`, coverage artefacts, and stray `*.docx` / `*.mhtml`. **`.venv/` is not deleted** unless you use **`pwsh -File scripts/clean_repo.ps1 -IncludeVenv`** or **`sh scripts/clean_repo.sh --include-venv`** (destructive). The **`.gitignore`** lists venvs, caches, and build artefacts so they are not committed.

## Quality tooling and CI

Configured in **`pyproject.toml`**; GitHub Actions runs **`.github/workflows/ci.yml`** on push/PR:

- `ruff check` (package `iav`; `scripts/` with per-file `E402` ignore where needed)
- `ruff format --check iav`
- `mypy` on `iav`
- `pytest` plus canonical verify, batch smoke, sensitivity report, annotated pilot, optional **music21** job

Run locally after `pip install -e ".[dev]"`.
