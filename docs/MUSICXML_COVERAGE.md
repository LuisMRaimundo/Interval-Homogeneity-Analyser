# MusicXML coverage and limitations

This document states what the **Interval_Homogeneity** does with real scores, based on
`validation/fixtures/`, `validation/corpus/`, and the parsers in `iav.musicxml_io`.

## Interpreted correctly (smoke-tested)

| Case | Fixture / note |
|------|----------------|
| Simple chords / aggregates | Manual entry + aggregate import |
| Ties (direct + notations) | `validation/fixtures/tie_*.xml` |
| Instrument transposition | `validation/fixtures/transpose.xml` — default **written** `<pitch>`; concert pitch via UI checkbox, CLI `--sounding-transpose`, or `parse_musicxml_upload` |
| Grace notes (optional include) | `validation/fixtures/grace.xml` |
| Multi-voice same measure | `validation/corpus/multi_voice_same_measure.xml` |
| Double-flats in encoding | `validation/corpus/double_flat_explicit.xml` |
| Backup / forward cursor | `validation/corpus/backup_forward_cursor.xml` |

## Normalized or simplified

- **Duplicate pitches** at the same quantized height may be collapsed when *Collapse to unique pitches* is on.
- **Spelling** follows parser rules (sharps lean in transpose variants); interval **sizes** use MIDI/cents, not note names.
- **Onset / sounding verticalities** reduce the score to slice-wise pitch lists; rhythmic detail beyond slice boundaries is not analysed.

## Ignored or out of scope

- **Audition, dynamics, timbre, registral dispersion maps** (use a separate tool).
- **Arpeggiation semantics** — arpeggiated chords may appear as successive slices, not as a simultaneous sonority, depending on import mode.
- **Tremolo / unpitched / percussion** — not treated as pitch-class sets.
- **Microtones** outside the selected EDO grid are quantized; some exports are skipped with a count in the UI.

## Passage analysis (time fragments)

Supported workflow for **active sections** (many attacks over time):

| Step | Setting |
|------|---------|
| Import | **Verticalities (onset slices)** or **Sounding verticalities** |
| Analysis | **All slices (summary)** or **Time window (summary)** |
| Output | **H vs time chart**, **vertical note-count chart** (Y = **`Notes`** only), table, **`slice_summary.csv`**, **`vertical_cardinality_profile.json`** (see §7.8 for JSON null rules when **PC cardinality** absent) |

**Not supported as a single timeline:** **Aggregate (all notes)** — pools the entire file into one verticality (warning when note count > 50). Use a trimmed XML excerpt only if you truly want one global pitch multiset. Aggregate/manual analysis still exports a **single-slice** cardinality JSON at time 0.

Implementation: `iav/musicxml.py` (orchestration), `iav/charts.py` (`chart_homogeneity_over_time`, `chart_vertical_cardinality_over_time`), `iav/vertical_cardinality.py`, `iav/symbolic_profile.py` (`passage_delta_rows`). See **TECHNICAL_MANUAL.md** §7.6–7.8. **How slice-level H relates to symbolic interval models (not audio):** [METRIC_SEMANTICS.md](METRIC_SEMANTICS.md) §10–§12.

## Requires caution

- **Crossed voices / divisi** — verticality slices may merge voices; check extracted pitch tables.
- **Extreme registers or wide spans** — pairwise entropy uses support `ln(span+1)`; compare aggregates with similar span when possible.
- **Enharmonic equivalence** — mod-12 tools (interval vector, prime form) use pitch class; pairwise tables use registral distances.

## Canonical regression scores (`validation/canonical/`)

Five minimal **aggregate** scores (one sonority each) with frozen metrics in `iav/data/canonical_musicxml.json`:

| File | Sonority role |
|------|----------------|
| `major_triad.xml` | Tertian triad (reference spelling) |
| `minor_triad.xml` | Minor triad |
| `chromatic_cluster.xml` | Dense semitone cluster |
| `quartal_stack.xml` | Stacked fourths |
| `diminished_seventh.xml` | Symmetric seventh chord |

Rebuild expectations: `python scripts/build_canonical_musicxml.py`. Tests: `tests/test_canonical_musicxml.py`.

## Regression (general)

- `tests/test_corpus_musicxml.py` — every file under `validation/fixtures/` and `validation/corpus/` must parse without crashing.
- `tests/test_canonical_musicxml.py` — canonical five-score suite (above).
- `python analyze_corpus.py --verify-canonical -i examples/corpus -o results/` — canonical JSON sonorities (no XML required for that verify step).

When adding a new MusicXML edge case, place the file under `validation/fixtures/` or `validation/corpus/` and extend this table. For a new **canonical** score, add under `validation/canonical/` and rerun the build script.
