# Interval_Homogeneity regression fixtures (phase 1)

Controlled symbolic fixtures and qualitative/metamorphic tests for **Interval_Homogeneity** (`iav`). Phase 1 validates **musicological semantics of interval distribution concentration** — not aesthetic judgment, not acoustic consonance, and not perceptual dissonance.

## Purpose

This suite guards against silent drift in:

- pairwise vs adjacent vs proximity-weighted vs hybrid homogeneity semantics;
- transposition and inversion invariance of distance-based metrics;
- cardinality vs interval-distribution distinctions;
- duplicate-pitch handling in manual aggregates;
- EDO / binning modelling choices;
- multi-slice passage profiles and ΔH along symbolic time.

**Phase 1 uses qualitative and metamorphic assertions only.** Scalar outputs are inspected in `corpus/reports/interval_homogeneity_regression_inspection.md` but are **not** locked as golden references yet.

## Symbolic / notational status

All fixtures are **symbolic pitch aggregates** represented as `(letter, alter, octave)` tuples or JSON-encoded equivalents. They describe **notated pitch-height relationships** on a selectable equal-division grid (`bin_cents`). They do **not** represent audio waveforms, spectra, or listener responses.

## Scope disclaimer

| In scope | Out of scope |
|----------|--------------|
| Interval-type concentration on an EDO grid | Acoustic consonance / roughness |
| Adjacent regularity after pitch-height sort | Psychoacoustic dissonance |
| Pairwise distance histogram shape | Harmonic-function or tonal interpretation |
| Metamorphic invariance (transposition, inversion multiset) | Performance timing or rubato |
| Passage-level ΔH between verticalities | Perceptual “beauty” or preference |

## Metric semantics (distinctions)

| Metric / field | Meaning in this suite |
|----------------|----------------------|
| `pair_score` | Dominance (or entropy) concentration of **all unordered pairwise absolute pitch distances** |
| `chain_score` | Same concentration measure on **adjacent intervals** after sorting by pitch height (also called adjacent regularity) |
| `weighted_linear_score` | Proximity-weighted pairs with weight **1/|i−j|** |
| `weighted_quadratic_score` | Proximity-weighted pairs with weight **1/|i−j|²** |
| `H` | Headline homogeneity; under default regression settings follows **pairwise** concentration |
| `hybrid_score` | α·adjacent + (1−α)·pairwise with α = 0.6 in default analysis block |
| `evenness_score` | Support-bounded Shannon evenness of the pairwise distance histogram |
| `distance_counts` / `adj_counts` | Empirical interval-distance histograms (modelling outputs) |

**Interval concentration ≠ consonance.** A minor-second dyad and a perfect-fifth dyad can both show **maximal single-interval concentration** because each has only one pairwise distance type. That result describes **distribution shape**, not pleasantness.

**Do not read H as an isolated scalar truth.** Always interpret alongside `distance_counts`, `adj_counts`, and the analysis configuration (`bin_cents`, `homogeneity_method`, headline mode).

## Dyad degeneracy

`unison_dyad` documents a **degenerate case**: two vertical events at the same pitch height. Vertical cardinality may be 2 while unique pitch content is 1. Pairwise concentration can be maximal by construction (one distance type: unison). This is **not** perceptual consonance validation.

## Cardinality vs interval distribution

`same_cardinality_different_distribution_A` and `same_cardinality_different_distribution_B` share note count (4) but differ in interval-distance profiles. Homogeneity metrics must **not** be inferred from cardinality alone.

## Duplicate pitches

`repeated_pitch_density_not_homogeneity` documents current manual-path behaviour:

- `metrics_for_notes` on the **raw** note list **preserves** duplicate pitch heights in interval counting.
- `dedupe_notes_by_midi` (used in MusicXML batch paths) **collapses** duplicate heights before analysis.

Tests assert the observed implementation; they do not invent deduplication policy.

## Octave equivalence

`octave_duplication_case` (C4, C5, G4) clarifies that the model uses **distinct pitch heights**; octave-related pitches are **not** collapsed to pitch class in homogeneity metrics.

## EDO / binning as modelling choice

`EDO_24_microtonal_regular` uses quarter-tone spellings with `bin_cents=50` (24-EDO).  
`EDO_bin_change_sensitivity` analyses the same chromatic segment at `bin_cents=100` vs `50`. Labels and H may change; bin width is a **modelling choice**, not performance tuning.

## File locations

| Path | Role |
|------|------|
| `corpus/fixtures/interval_homogeneity_regression/*.json` | Fixture definitions |
| `corpus/fixtures/interval_homogeneity_regression/manifest.json` | Fixture index |
| `corpus/scripts/create_interval_homogeneity_regression_fixtures.py` | Deterministic generator |
| `corpus/scripts/inspect_interval_homogeneity_regression.py` | Exploratory inspection report |
| `corpus/reports/interval_homogeneity_regression_inspection.md` | Human-readable metrics snapshot |
| `corpus/reports/interval_homogeneity_regression_inspection.json` | Machine-readable inspection |
| `tests/test_interval_homogeneity_regression_fixtures.py` | Qualitative pytest suite |

Regenerate fixtures:

```bash
python corpus/scripts/create_interval_homogeneity_regression_fixtures.py
python corpus/scripts/inspect_interval_homogeneity_regression.py
```

## Default analysis block (fixtures)

```json
{
  "homogeneity_method": "dominance",
  "bin_cents": 100,
  "hybrid_alpha": 0.6,
  "dominance_threshold": 0.35,
  "even_high": 0.8,
  "even_low": 0.3,
  "chain_threshold": 0.60,
  "intervallic_headline_mode": "pairwise_intervallic_concentration"
}
```

## Fixture catalogue

### 1. `unison_dyad`

- **Notes:** C4, C4  
- **Expected (qualitative):** vertical count 2, unique pitch height 1; maximally concentrated single distance type; degenerate/simple case.  
- **Not:** perceptual consonance validation.

### 2. `single_interval_dyad_perfect_fifth`

- **Notes:** C4, G4  
- **Expected:** one pairwise interval type; high/maximal `pair_score` by construction.  
- **Not:** acoustic consonance proof.

### 3. `minor_second_dyad`

- **Notes:** C4, C#4  
- **Expected:** same single-interval concentration logic as the fifth dyad.  
- **Demonstrates:** homogeneity ≠ consonance.

### 4. `chromatic_cluster_four`

- **Notes:** C4, C#4, D4, D#4  
- **Expected:** regular adjacent semitones; more diverse pairwise set; `chain_score` > `pair_score`.

### 5. `whole_tone_segment_four`

- **Notes:** C4, D4, E4, F#4  
- **Expected:** uniform whole-tone adjacent spacing; broader pairwise distances; adjacent vs pairwise distinction.

### 6. `stacked_fourths`

- **Notes:** C4, F4, Bb4, Eb5  
- **Expected:** repeated P4 adjacent intervals; wider compound pairwise relations.

### 7. `stacked_fifths`

- **Notes:** C3, G3, D4, A4  
- **Expected:** repeated P5 adjacent intervals; compare interval-type concentration with `stacked_fourths`.

### 8. `major_triad_close`

- **Notes:** C4, E4, G4  
- **Expected:** multiple pairwise interval types; not maximally homogeneous; compare with `augmented_triad_symmetric`.

### 9. `augmented_triad_symmetric`

- **Notes:** C4, E4, G#4  
- **Expected:** stronger interval-type regularity than major triad under pairwise logic.  
- **Not:** perceptual equivalence claim.

### 10. `diminished_seventh_symmetric`

- **Notes:** C4, Eb4, Gb4, A4  
- **Expected:** symmetric equal minor-third division; high adjacent regularity.

### 11. `dominant_seventh_irregular`

- **Notes:** C4, E4, G4, Bb4  
- **Expected:** same cardinality as dim7; more diverse pairwise profile.

### 12. `same_cardinality_different_distribution_A`

- **Notes:** C4, D4, E4, F4  
- **Expected:** compact scalar cluster; distinct distribution from fixture B.

### 13. `same_cardinality_different_distribution_B`

- **Notes:** C4, E4, G#4, C5  
- **Expected:** same cardinality (4); different interval distribution.

### 14. `octave_duplication_case`

- **Notes:** C4, C5, G4  
- **Expected:** octave-related heights treated as distinct; affects pairwise histogram.

### 15. `transposed_same_structure`

- **Notes:** D4, D#4, E4, F#4 (transposition of `chromatic_cluster_four`)  
- **Expected:** `pair_score`, `chain_score`, `H`, `hybrid_score` invariant within tolerance.

### 16. `inversion_same_interval_multiset`

- **Notes:** E4, G#4, C#4 (inversional counterpart of `major_triad_close` around E4)  
- **Expected:** pairwise distance multiset preserved; distance-based homogeneity stable.

### 17. `EDO_24_microtonal_regular`

- **Notes:** C4, C+0.5, D4, D+0.5 with `bin_cents=50`  
- **Expected:** no crash; coherent quarter-tone grid labels; stable qualitative relations only.

### 18. `EDO_bin_change_sensitivity`

- **Notes:** chromatic cluster; analysed at `bin_cents` 100 and 50  
- **Expected:** labels and/or metrics may differ; documents binning as modelling choice.

### 19. `repeated_pitch_density_not_homogeneity`

- **Notes:** C4, C4, C4, G4  
- **Expected:** raw aggregate preserves duplicates; dedupe path collapses to C4+G4 dyad.

### 20. `passage_changing_interval_field`

- **Slices:** chromatic cluster → whole-tone segment → diminished seventh  
- **Expected:** multiple passage rows; changing interval profiles; ΔH column populated where implemented.

## Qualitative-only expectations (phase 1)

The following are asserted qualitatively in tests, **not** as frozen scalars:

- dyad single-interval concentration (fifth and minor second);
- `chain_score` > `pair_score` for chromatic / whole-tone tetrachords;
- symmetric > irregular chord concentration ordering (dim7 vs dom7; aug vs major);
- transposition invariance of distance metrics;
- inversion multiset preservation;
- duplicate-pitch policy (raw vs deduped);
- passage interval-profile change across slices;
- documentation completeness for every fixture id.

## Phase 2 (not in scope yet)

Promoting selected inspection values to frozen golden JSON (as in `iav/data/canonical_sonorities.json`) requires an explicit decision record and licensed-corpus review. Do not copy phase-1 inspection numbers into strict regression without that review.
