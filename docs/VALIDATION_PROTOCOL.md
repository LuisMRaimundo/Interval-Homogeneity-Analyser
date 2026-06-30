# Validation protocol — Intervallic_Homogeneity

## What this tool measures

The Intervallic_Homogeneity computes **symbolic intervallic homogeneity** on notated pitch aggregates:

- unordered pairwise absolute pitch distances on a declared EDO grid;
- optional adjacent, proximity-weighted, hybrid, and combined headline modes (see `TECHNICAL_MANUAL.md` §4–§5).

Inputs are **spellings and score times** (manual table or MusicXML). Outputs are interval histograms, concentration scores, optional passage timelines (intervallic **H** and vertical **note-count** profiles), and **`vertical_cardinality_profile.json`** — not listener responses.

**Metric semantics and interpretive limits:** [METRIC_SEMANTICS.md](METRIC_SEMANTICS.md).

## What this tool does **not** measure

Human labels and automated metrics in validation studies must **not** be interpreted as:

- perceptual consonance or dissonance;
- psychoacoustic roughness or sensory dissonance;
- acoustic timbre, fusion, or brightness;
- registral dispersion, register band occupation, or vertical registral layout (use a dedicated registral tool);
- acoustic density, loudness, spectral mass, or perceptual fusion (vertical cardinality here is **symbolic note thickness** only);
- pitch-class cardinality inferred from unique-pitch count in exports (the app sets JSON **`vertical_pitch_class_cardinality`** to **`null`** unless **PC cardinality** is explicit in the slice row — see **TECHNICAL_MANUAL.md** §7.8).

**Human `texture_class` / `expected_headline_mode` fields are analytical judgements** for protocol checking (agreement with a stated symbolic stance), not ground truth for how music “sounds.”

## Annotation file format

CSV (UTF-8) with header row. Required columns:

| Column | Description |
|--------|-------------|
| `case_id` | Unique identifier (matches batch `source_id` when applicable) |
| `texture_class` | One of: `homogeneous`, `heterogeneous`, `local_regular` (extend only with documented protocol revision) |
| `rater_id` | Annotator id (`rater_a`, `rater_b`, …) |

Optional columns:

| Column | Description |
|--------|-------------|
| `notes` | Free-text analyst comment |
| `expected_headline_mode` | Symbolic expectation for protocol audit (not enforced by the engine) |
| `source_file` | Path hint for traceability |

Multiple rows per `case_id` with different `rater_id` enable Cohen’s κ.

## Automated comparison fields

`scripts/validation_report.py` joins annotations to batch or inline metrics and reports:

- descriptive counts per `texture_class`;
- confusion matrix: human `texture_class` vs tool `classification` string;
- Cohen’s κ when two raters exist for the same `case_id`;
- Spearman ρ between human ordinal proxies and numeric `headline_H` **only if** `scipy` is installed (otherwise skipped with a log message).

## Reproducibility checklist

1. Record `package_version` / git commit and exact analysis preset (`ANALYSIS_PRESET.md`).
2. Archive `config_used.json` from batch runs.
3. State register/EDO, headline mode, homogeneity scoring, and MusicXML import mode in methods text.
4. Distinguish **H** from occupancy-style exploratory columns and from heatmap-style density maps (not produced here).
5. Do not claim perceptual validation from κ or ρ alone without a separate listening study.

## Synthetic fixtures

`tests/fixtures/validation_annotations_minimal.csv` supports CI for the report script without a large corpus.
