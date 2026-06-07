# Interval homogeneity regression — exploratory inspection (phase 1)

Generated: 2026-06-07T21:12:34Z

These values are **exploratory** only. Do not promote them to strict golden references.

## unison_dyad

**Description:** Degenerate dyad: duplicate C4. Two vertical events, one unique pitch height.

- Notes: `[['C', 0.0, 4], ['C', 0.0, 4]]`
- Cardinality: 2; unique pitches: 1
- pair_score: 1.0; chain_score: 1.0
- weighted_linear_score: 1.0
- hybrid_score: 1.0; H: 1.0; H_label: homogeneous
- evenness_score: 0.0; classification: P1-dominant; low evenness; uniform stacking
- distance_counts: {'0': 1}
- adj_counts: {'0': 1}
- Note: Single-interval or maximally concentrated dyad/degenerate case (not consonance validation).

## single_interval_dyad_perfect_fifth

**Description:** Dyad C4–G4: one pairwise interval type (P5 on 12-TET grid).

- Notes: `[['C', 0.0, 4], ['G', 0.0, 4]]`
- Cardinality: 2; unique pitches: 2
- pair_score: 1.0; chain_score: 1.0
- weighted_linear_score: 1.0
- hybrid_score: 1.0; H: 1.0; H_label: homogeneous
- evenness_score: 0.0; classification: P5-dominant; low evenness; uniform stacking
- distance_counts: {'7': 1}
- adj_counts: {'7': 1}
- Note: Single-interval or maximally concentrated dyad/degenerate case (not consonance validation).

## minor_second_dyad

**Description:** Dyad C4–C#4: single m2 interval; high concentration does not imply consonance.

- Notes: `[['C', 0.0, 4], ['C', 1.0, 4]]`
- Cardinality: 2; unique pitches: 2
- pair_score: 1.0; chain_score: 1.0
- weighted_linear_score: 1.0
- hybrid_score: 1.0; H: 1.0; H_label: homogeneous
- evenness_score: 0.0; classification: m2-dominant; low evenness; uniform stacking
- distance_counts: {'1': 1}
- adj_counts: {'1': 1}
- Note: Single-interval or maximally concentrated dyad/degenerate case (not consonance validation).

## chromatic_cluster_four

**Description:** Four consecutive semitones C4–D#4: regular adjacent spacing, diverse pairwise set.

- Notes: `[['C', 0.0, 4], ['C', 1.0, 4], ['D', 0.0, 4], ['D', 1.0, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.5; chain_score: 1.0
- weighted_linear_score: 0.692308
- hybrid_score: 0.8; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.729574; classification: m2-dominant; mid evenness; uniform stacking
- distance_counts: {'1': 3, '2': 2, '3': 1}
- adj_counts: {'1': 3}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## whole_tone_segment_four

**Description:** Whole-tone segment C4–F#4: uniform adjacent M2, broader pairwise distances.

- Notes: `[['C', 0.0, 4], ['D', 0.0, 4], ['E', 0.0, 4], ['F', 1.0, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.5; chain_score: 1.0
- weighted_linear_score: 0.692308
- hybrid_score: 0.8; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.519759; classification: M2-dominant; mid evenness; uniform stacking
- distance_counts: {'2': 3, '4': 2, '6': 1}
- adj_counts: {'2': 3}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## stacked_fourths

**Description:** Quartal stack C4–Eb5: repeated P4 adjacent intervals.

- Notes: `[['C', 0.0, 4], ['F', 0.0, 4], ['B', -1.0, 4], ['E', -1.0, 5]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.5; chain_score: 1.0
- weighted_linear_score: 0.692308
- hybrid_score: 0.8; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.364787; classification: P4-dominant; mid evenness; uniform stacking
- distance_counts: {'5': 3, '10': 2, '15': 1}
- adj_counts: {'5': 3}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## stacked_fifths

**Description:** Fifths stack C3–A4: repeated P5 adjacent intervals.

- Notes: `[['C', 0.0, 3], ['G', 0.0, 3], ['D', 0.0, 4], ['A', 0.0, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.5; chain_score: 1.0
- weighted_linear_score: 0.692308
- hybrid_score: 0.8; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.327205; classification: P5-dominant; mid evenness; uniform stacking
- distance_counts: {'7': 3, '14': 2, '21': 1}
- adj_counts: {'7': 3}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## major_triad_close

**Description:** Closed major triad C4–E4–G4: three distinct pairwise interval types.

- Notes: `[['C', 0.0, 4], ['E', 0.0, 4], ['G', 0.0, 4]]`
- Cardinality: 3; unique pitches: 3
- pair_score: 0.333333; chain_score: 0.5
- weighted_linear_score: 0.4
- hybrid_score: 0.433333; H: 0.333333; H_label: moderately heterogeneous
- evenness_score: 0.528321; classification: no dominant interval; mid evenness; irregular stacking
- distance_counts: {'4': 1, '7': 1, '3': 1}
- adj_counts: {'4': 1, '3': 1}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## augmented_triad_symmetric

**Description:** Augmented triad C4–E4–G#4: equal major-third division in 12-TET.

- Notes: `[['C', 0.0, 4], ['E', 0.0, 4], ['G', 1.0, 4]]`
- Cardinality: 3; unique pitches: 3
- pair_score: 0.666667; chain_score: 1.0
- weighted_linear_score: 0.8
- hybrid_score: 0.866667; H: 0.666667; H_label: moderately homogeneous
- evenness_score: 0.28969; classification: M3-dominant; low evenness; uniform stacking
- distance_counts: {'4': 2, '8': 1}
- adj_counts: {'4': 2}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## diminished_seventh_symmetric

**Description:** Diminished seventh C4–A4: symmetric minor-third tiling.

- Notes: `[['C', 0.0, 4], ['E', -1.0, 4], ['G', -1.0, 4], ['A', 0.0, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.5; chain_score: 1.0
- weighted_linear_score: 0.692308
- hybrid_score: 0.8; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.439247; classification: m3-dominant; mid evenness; uniform stacking
- distance_counts: {'3': 3, '6': 2, '9': 1}
- adj_counts: {'3': 3}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## dominant_seventh_irregular

**Description:** Dominant seventh C4–Bb4: same cardinality as dim7, less regular pairwise profile.

- Notes: `[['C', 0.0, 4], ['E', 0.0, 4], ['G', 0.0, 4], ['B', -1.0, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.333333; chain_score: 0.666667
- weighted_linear_score: 0.461538
- hybrid_score: 0.533333; H: 0.333333; H_label: moderately heterogeneous
- evenness_score: 0.650867; classification: no dominant interval; mid evenness; predominantly regular stacking
- distance_counts: {'4': 1, '7': 1, '10': 1, '3': 2, '6': 1}
- adj_counts: {'4': 1, '3': 2}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## same_cardinality_different_distribution_A

**Description:** Four-note diatonic cluster C4–F4: compact scalar / adjacent regularity.

- Notes: `[['C', 0.0, 4], ['D', 0.0, 4], ['E', 0.0, 4], ['F', 0.0, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.333333; chain_score: 0.666667
- weighted_linear_score: 0.461538
- hybrid_score: 0.533333; H: 0.333333; H_label: moderately heterogeneous
- evenness_score: 0.871049; classification: no dominant interval; high evenness; predominantly regular stacking
- distance_counts: {'2': 2, '4': 1, '5': 1, '3': 1, '1': 1}
- adj_counts: {'2': 2, '1': 1}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## same_cardinality_different_distribution_B

**Description:** Four-note wide/symmetric C4–C5: same cardinality, different interval distribution.

- Notes: `[['C', 0.0, 4], ['E', 0.0, 4], ['G', 1.0, 4], ['C', 0.0, 5]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.5; chain_score: 1.0
- weighted_linear_score: 0.692308
- hybrid_score: 0.8; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.394317; classification: M3-dominant; mid evenness; uniform stacking
- distance_counts: {'4': 3, '8': 2, '12': 1}
- adj_counts: {'4': 3}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## octave_duplication_case

**Description:** C4 C5 G4: octave duplication; model uses distinct pitch heights (no pc collapse).

- Notes: `[['C', 0.0, 4], ['C', 0.0, 5], ['G', 0.0, 4]]`
- Cardinality: 3; unique pitches: 3
- pair_score: 0.333333; chain_score: 0.5
- weighted_linear_score: 0.4
- hybrid_score: 0.433333; H: 0.333333; H_label: moderately heterogeneous
- evenness_score: 0.428317; classification: no dominant interval; mid evenness; irregular stacking
- distance_counts: {'12': 1, '7': 1, '5': 1}
- adj_counts: {'7': 1, '5': 1}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## transposed_same_structure

**Description:** chromatic_cluster_four transposed up major second (D4–F#4).

- Notes: `[['D', 0.0, 4], ['D', 1.0, 4], ['E', 0.0, 4], ['E', 1.0, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.5; chain_score: 1.0
- weighted_linear_score: 0.692308
- hybrid_score: 0.8; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.729574; classification: m2-dominant; mid evenness; uniform stacking
- distance_counts: {'1': 3, '2': 2, '3': 1}
- adj_counts: {'1': 3}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## inversion_same_interval_multiset

**Description:** Inversion of major_triad_close around E4: E4 G#4 C#4.

- Notes: `[['E', 0.0, 4], ['G', 1.0, 4], ['C', 1.0, 4]]`
- Cardinality: 3; unique pitches: 3
- pair_score: 0.333333; chain_score: 0.5
- weighted_linear_score: 0.4
- hybrid_score: 0.433333; H: 0.333333; H_label: moderately heterogeneous
- evenness_score: 0.528321; classification: no dominant interval; mid evenness; irregular stacking
- distance_counts: {'4': 1, '3': 1, '7': 1}
- adj_counts: {'3': 1, '4': 1}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## EDO_24_microtonal_regular

**Description:** Quarter-tone chromatic segment on 24-EDO grid (bin_cents=50).

- Notes: `[['C', 0.0, 4], ['C', 0.5, 4], ['D', 0.0, 4], ['D', 0.5, 4]]`
- Cardinality: 4; unique pitches: 4
- pair_score: 0.333333; chain_score: 0.666667
- weighted_linear_score: 0.461538
- hybrid_score: 0.533333; H: 0.333333; H_label: moderately heterogeneous
- evenness_score: 0.742098; classification: no dominant interval; mid evenness; predominantly regular stacking
- distance_counts: {'1': 2, '4': 2, '5': 1, '3': 1}
- adj_counts: {'1': 2, '3': 1}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## EDO_bin_change_sensitivity

**Description:** Same four semitones analysed at bin_cents=100 vs 50 (modelling choice).

### bin_cents=100
- H: 0.5; pair_score: 0.5; chain_score: 1.0
- distance_counts: {'1': 3, '2': 2, '3': 1}

### bin_cents=50
- H: 0.5; pair_score: 0.5; chain_score: 1.0
- distance_counts: {'2': 3, '4': 2, '6': 1}

## repeated_pitch_density_not_homogeneity

**Description:** C4 C4 C4 G4: duplicate pitches preserved in manual aggregate path.

- Notes: `[['C', 0.0, 4], ['C', 0.0, 4], ['C', 0.0, 4], ['G', 0.0, 4]]`
- Cardinality: 4; unique pitches: 2
- pair_score: 0.5; chain_score: 0.666667
- weighted_linear_score: 0.576923
- hybrid_score: 0.6; H: 0.5; H_label: moderately homogeneous
- evenness_score: 0.333333; classification: P1-dominant; mid evenness; predominantly regular stacking
- distance_counts: {'0': 3, '7': 3}
- adj_counts: {'0': 2, '7': 1}
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

## passage_changing_interval_field

**Description:** Three verticalities: chromatic cluster, whole-tone segment, diminished seventh.

### Slice 1: chromatic_cluster
- Notes: `[['C', 0.0, 4], ['C', 1.0, 4], ['D', 0.0, 4], ['D', 1.0, 4]]`
- H: 0.5; pair_score: 0.5; chain_score: 1.0
- hybrid_score: 0.8; evenness: 0.729574
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

### Slice 2: whole_tone_segment
- Notes: `[['C', 0.0, 4], ['D', 0.0, 4], ['E', 0.0, 4], ['F', 1.0, 4]]`
- H: 0.5; pair_score: 0.5; chain_score: 1.0
- hybrid_score: 0.8; evenness: 0.519759
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

### Slice 3: diminished_seventh
- Notes: `[['C', 0.0, 4], ['E', -1.0, 4], ['G', -1.0, 4], ['A', 0.0, 4]]`
- H: 0.5; pair_score: 0.5; chain_score: 1.0
- hybrid_score: 0.8; evenness: 0.439247
- Note: Adjacent regularity exceeds pairwise concentration under current semantics.

- interval_profile_changes: True

