# Metric semantics — Interval_Homogeneity

**Purpose:** Clarify what the main intervallic homogeneity metrics **mean**, how they are **computed** (at a conceptual level), what they **do not** measure, and how they may support **musicological** reading. This document is interpretive; algorithmic detail and UI parameters remain in [TECHNICAL_MANUAL.md](../TECHNICAL_MANUAL.md).

**Related:** [QUICK_GUIDE.md](../QUICK_GUIDE.md) (interface), [ANALYSIS_PRESET.md](../ANALYSIS_PRESET.md) (fixed presets), [docs/MUSICXML_COVERAGE.md](MUSICXML_COVERAGE.md) (parser scope), [docs/ARCHITECTURE.md](ARCHITECTURE.md) (code layout).

---

## 1. Scope and methodological status

Interval_Homogeneity computes **symbolic / notational descriptors** of **intervallic organisation** in:

- **note aggregates** (manual entry or MusicXML aggregate mode),
- **verticalities** (onset or sounding slices from MusicXML),
- **passage profiles** (sequences of slice-level metrics over score time),
- **manually entered sonorities** (chord lists without a full score parser).

The tool measures **intervallic regularity, concentration, and diversity** under **declared symbolic interval models** implemented in `iav.interval_analysis_core` and related modules. Results are **model-dependent summaries**, not intrinsic properties of sounding music.

### What this tool is **not**

| Category | Status |
|----------|--------|
| Audio / waveform analysis | **Not supported** |
| Spectral analysis (FFT, partials, formants) | **Not supported** |
| Psychoacoustic consonance / sensory dissonance | **Not modelled** |
| Perceptual validation / listener studies | **Not included** |
| Loudness, timbre, masking, beating, roughness | **Not measured** |
| Orchestration weight / blend / balance | **Not measured** |
| Automatic musicological interpretation | **Not provided** |

The application operates on **notated pitch spellings** and **score-time structure** extracted from manual tables or MusicXML. It does **not** substitute for musical judgement, performance analysis, or acoustic measurement.

---

## 2. Core vocabulary

### Note tuple (`NoteTuple`)

A pitched note as **`(letter, alter, octave)`**:

- `letter` ∈ {C, D, E, F, G, A, B}
- `alter` — semitone offset from the natural letter (may be fractional for microtones)
- `octave` — octave number in the same convention as MusicXML / manual entry (middle C = **C4**)

**Sonic height** for intervals is always derived from this tuple via `chromatic_midi_float`, then quantised to analysis units (see §9).

### Pitch unit / analysis unit

After quantisation, each note maps to an integer **unit** `U(n)` on the selected EDO grid (`note_to_units`). Pairwise and adjacent intervals are computed on these **units**, not on raw spellings alone.

### EDO and `bin_cents`

- **EDO** (*equal division of the octave*): user-selectable grid (**12, 24, or 48** in the app and batch CLI).
- **`bin_cents`** = `round(1200 / EDO)` — cents per one grid step (100, 50, or 25 for the three supported EDOs).

EDO selection is **symbolic quantisation**, not a claim about how an ensemble is tuned in performance.

### Semitone distance

For `bin_cents = 100` (12-EDO), one unit corresponds to one **12-TET semitone** of absolute pitch height. Pairwise analysis uses **absolute** distance `|U_i − U_j|`, not octave-reduced pitch-class distance (unless you separately use §6 set-class tools).

### Interval, interval label, interval class

- **Interval (operational):** absolute grid distance between two quantised pitch units.
- **Interval label (`interval_counts` keys):** human-readable name from `units_to_label` / `semitone_to_label` when `bin_cents = 100` (e.g. `M3`, `P5`, `TT4`); otherwise a **cents string** (e.g. `50c` on a 24-EDO grid).
- **Interval class (mod 12):** in Forte set-class tools only — unordered pitch-class distance class 1…6 (`interval_vector_12tet`). **Not** the same as pairwise interval labels on spelled height.

### Pairwise interval

For **N** notes, **all unordered pairs** `{i, j}` with `i < j`. Each pair contributes one absolute distance to `distance_counts` and one string label to `interval_counts`. Count = **N(N−1)/2**.

### Adjacent interval (chain interval)

After **sorting** notes by quantised height `U_1 ≤ … ≤ U_N`, **consecutive gaps** `U_{k+1} − U_k`. This is **not** score order, voice-leading, or partwise motion — only **melodic chain through sorted register**.

**Code name:** `chain_score`, `adj_counts` (historical “chain” terminology).

### Proximity-weighted interval

All unordered pairs after sorting, but pair `(i, j)` with `i < j` receives weight **`1 / (j − i)^p`** (`p = 1` linear, `p = 2` quadratic). Weights accumulate into a **float** distance histogram. **Not** an auditory masking model — a **symbolic** emphasis on locally adjacent pitch pairs in sorted order.

### Aggregate, sonority, verticality, slice

| Term | Meaning |
|------|---------|
| **Aggregate** | One finite multiset of notes analysed as a **single** sonority (manual table or MusicXML aggregate mode). |
| **Sonority** | Informal name for one aggregate under analysis. |
| **Verticality** | A **time-slice** of notes that sound together (or at an onset) in MusicXML verticality modes. |
| **Slice** | One verticality instance with its own note list and metrics; passage mode produces **many slices**. |

### Interval-count distribution and distance histogram

- **`interval_counts`:** histogram keyed by **string interval labels** (pairwise).
- **`distance_counts`:** histogram keyed by **integer absolute distance** in grid units (pairwise).
- **`adj_counts`:** histogram of **adjacent gaps** after sorting.

### Headline metric, **H**, **H_label**, classification

- **Headline metric:** the single concentration score selected as **H** via `IntervallicHeadlineMode` (pairwise, adjacent, weighted, or hybrid).
- **H:** headline **intervallic homogeneity** in **[0, 1]** (higher = more concentrated / regular under the chosen model).
- **H_label:** categorical band from fixed thresholds (`homogeneous`, `moderately homogeneous`, …) — see [TECHNICAL_MANUAL.md §5.3](../TECHNICAL_MANUAL.md).
- **classification:** semicolon-separated **heuristic** English summary (dominant interval clause, evenness band, stacking clause).

### Spelling vs distance; written vs sounding; manual vs MusicXML; verticality vs passage

| Distinction | Clarification |
|-------------|---------------|
| **Spelling vs distance** | Enharmonic spellings that collapse to the same grid unit yield the **same** interval distances and labels. |
| **Written vs sounding** | Default MusicXML import uses **written** `<pitch>`. **Concert pitch** applies `<transpose>` and may **respell** to sharp-leaning canonical form — sounding height preserved, orthography not. |
| **Manual vs MusicXML verticalities** | Manual entry is one aggregate. MusicXML can yield **many slices** over time. |
| **Slice vs passage profile** | One slice → one **H**. Passage modes add **ΔH (prev slice)** and timeline charts across slices. |

---

## 3. Pairwise interval homogeneity (`pair_score`)

### Semantics

- Considers **every unordered pair** of notes in the aggregate.
- Builds **`distance_counts`** (integer keys) and **`interval_counts`** (string labels).
- **`pair_score`** = **intervallic concentration** of the pairwise distance histogram:
  - **Dominance method:** maximum bin share (§7).
  - **Entropy method:** `1 − Evenness_sup(distance_counts)` (§7, [TECHNICAL_MANUAL.md §4.4](../TECHNICAL_MANUAL.md)).

### Sensitive to

The **full internal distribution** of absolute pitch distances — remote intervals matter as much as local ones (unlike adjacent or proximity-weighted views).

### Not the same as

- **Adjacent regularity** (`chain_score`) — sorted consecutive gaps only.
- **Pitch-class set structure** — pairwise labels use **absolute height**, not mod-12 class alone.
- **Perceptual consonance** — a high `pair_score` means **one distance class dominates the pair histogram**, not “sounds consonant.”

### Duplicates and cardinality

With **deduplication** enabled (`dedupe_notes_by_midi`), repeated spellings at the **same grid unit** collapse to the first occurrence (order-dependent). Without dedupe, duplicate units create **more pairs** at distance zero. **Vertical cardinality** (note count per slice) is separate from **H** — see §12.

---

## 4. Adjacent interval homogeneity (`chain_score`)

### Semantics

1. Sort notes by quantised height.
2. Compute gaps between **consecutive** sorted pitches.
3. Build **`adj_counts`**.
4. **`chain_score`** = concentration of `adj_counts` (dominance or entropy path, same as pairwise).

### Interpretation

Measures **stepwise internal regularity** / **ordered spacing** through register — “generative” or **local** regularity after sorting.

### Typical divergence from pairwise

A sonority may show **high `chain_score`** (repeated semitone steps in a chromatic cluster) while **`pair_score`** stays lower (many distinct pairwise distances). See §14.

**UI label:** *Adjacent intervallic regularity*.

---

## 5. Proximity-weighted interval homogeneity

Two subscores are always computed:

| Field | Weight exponent `p` |
|-------|---------------------|
| **`weighted_linear_score`** | `p = 1` → weight `1/(j−i)` |
| **`weighted_quadratic_score`** | `p = 2` → weight `1/(j−i)²` |

Concentration uses **`dominance_weighted`** or **`entropy_evenness_supportbounded_weighted`** on the float histogram.

### Interpretation

- Emphasises **near neighbours** in **sorted pitch order**.
- **Not** psychoacoustic salience, masking, or orchestration proximity.
- Read as a **symbolic weighting strategy** between “all pairs equal” (pairwise) and “only consecutive gaps” (adjacent).

Either weighted score can be selected as **headline H** via `IntervallicHeadlineMode.WEIGHTED_LINEAR` or `WEIGHTED_QUADRATIC`.

---

## 6. Hybrid score (`hybrid_score` and hybrid headline **H**)

When headline mode is **Hybrid** (`hybrid_intervallic_homogeneity`):

$$
H = \alpha \cdot S_{\mathrm{chain}} + (1 - \alpha) \cdot S_{\mathrm{pair}}
$$

where `S_chain` = `chain_score`, `S_pair` = `pair_score`, and **α** is clamped to **[0, 1]** in `resolve_headline_h`.

| α | Effect (implementation) |
|---|-------------------------|
| **α = 1** | Headline **H** = adjacent (`chain_score`) only |
| **α = 0** | Headline **H** = pairwise (`pair_score`) only |
| **0 < α < 1** | Convex blend of the two concentrations |

**`hybrid_score`** in canonical / export bundles is the same blend formula applied to the underlying subscores (see `analyze_sonority`).

### `auto_alpha` and `k_auto`

When **`auto_alpha`** is enabled and there are **≥ 3** notes:

$$
\alpha_{\mathrm{used}} = \alpha_{\mathrm{base}} + (1 - \alpha_{\mathrm{base}}) \cdot \frac{n_{\mathrm{adj}} - 1}{(n_{\mathrm{adj}} - 1) + k_{\mathrm{auto}}}
$$

with `n_adj = max(1, N − 1)`. This **increases α toward 1** as the sorted chain lengthens — a **model parameter**, not an empirically calibrated perceptual tuning.

**Invalid α:** `homogeneity_score` raises `ValueError` if α ∉ [0, 1].

---

## 7. Dominance, entropy, evenness, and type concentration

### Dominance (`dominance`, `dominance_weighted`)

$$
\mathrm{Dominance} = \frac{\max_r c_r}{\sum_r c_r}
$$

Maximum category share in a histogram. **High dominance** ⇒ one interval distance (or gap) accounts for most of the multiset.

### Entropy and evenness

**Shannon entropy** (natural log):

$$
H_{\mathrm{ent}} = -\sum_{r:\, p_r > 0} p_r \ln p_r
$$

**Support-bounded evenness** (production path for `evenness_score` and entropy-method concentrations):

$$
\mathrm{Evenness}_{\mathrm{sup}} = \min\!\left(1,\, \frac{H_{\mathrm{ent}}}{H_{\mathrm{sup}}}\right), \quad H_{\mathrm{sup}} = \ln(\texttt{support\_bins})
$$

with `support_bins = max(1, span + 1)` from the aggregate’s pitch span in grid units ([TECHNICAL_MANUAL.md §4.4](../TECHNICAL_MANUAL.md)).

**Entropy concentration subscore:** `1 − Evenness_sup`.

**Exploratory `entropy_evenness`** (Pielou-style, denominator `ln K` for **observed** categories only) is used mainly as a **fallback** in `classify_aggregate` when pairwise evenness is not supplied — **not** for headline entropy mode.

### Type concentration (`type_score`)

On **labeled** pairwise intervals (`interval_counts`):

$$
\mathrm{TypeConcentration} = 1 - \frac{K - 1}{T - 1}
$$

for `T > 1` distinct pair labels with total count `T`; custom index — **not** a standard ecological diversity measure.

### Key interpretive points

| Statement | Detail |
|-----------|--------|
| **High evenness ≠ high homogeneity** | Evenness measures **spread**; homogeneity **H** measures **concentration** (dominance) or **1 − evenness** (entropy path). |
| **Low diversity may imply dominance** | Does **not** imply consonance, beauty, or stability. |
| **Dyad** | One pairwise interval ⇒ dominance concentration **1.0** by construction (trivial saturation). |

---

## 8. Headline modes and **H**

### Headline modes (`IntervallicHeadlineMode`)

| Mode | **H** equals |
|------|----------------|
| Pairwise (default) | `pair_score` |
| Adjacent | `chain_score` |
| Weighted linear | `weighted_linear_score` |
| Weighted quadratic | `weighted_quadratic_score` |
| Hybrid | `α·chain + (1−α)·pair` |

### Homogeneity methods (`homogeneity_method`)

| Method | Subscore construction |
|--------|----------------------|
| **dominance** | Maximum share |
| **entropy** | `1 − Evenness_sup` |
| **combined** | Computes both paths; headline **`H_consensus`** = geometric mean √(H_dom · H_ent) (after clamping negatives to 0) |

### **H**, **H_label**, consensus

- **H** is a **model summary**, not an objective truth about the musical object.
- **H** depends on: EDO / `bin_cents`, deduplication, import mode, headline mode, homogeneity method, α, thresholds, and (for MusicXML) parser options.
- **`H_label`:** fixed bands on **H** only — independent of the long `classification` string.
- **Consensus (`H_consensus`):** only in **combined** method — reconciles dominance- and entropy-path headlines.

**Interval heterogeneity** in the UI = **`1 − H`** (display convention).

---

## 9. EDO and binning semantics

| EDO | `bin_cents` | One unit step |
|-----|-------------|---------------|
| 12 | 100 | 1 semitone |
| 24 | 50 | 1 quarter-tone step |
| 48 | 25 | 1 eighth-tone step |

**Quantisation:** `U(n) = quantize_units(cents(n) / bin_cents)` with asymmetric half-up rounding ([TECHNICAL_MANUAL.md §2.4](../TECHNICAL_MANUAL.md)).

**Functions:** `note_to_units`, `units_to_label`, `semitone_to_label`, `intervals_for_notes`.

### Limits

- **Not** performance tuning analysis — symbolic grid only.
- Microtonal spellings are represented only insofar as they survive quantisation on the chosen EDO.
- Changing **EDO** or **`bin_cents`** can change labels, histograms, and **H**.

---

## 10. MusicXML import semantics

See [TECHNICAL_MANUAL.md §7](../TECHNICAL_MANUAL.md) and [MUSICXML_COVERAGE.md](MUSICXML_COVERAGE.md).

| Mode | Behaviour |
|------|-----------|
| **Aggregate** | All pitched notes → **one** sonority (pooled; no time slicing). |
| **Onset verticalities** | Chord slices at **attack times** per voice/measure logic. |
| **Sounding verticalities** | Slices from **sustained** notes (duration > 0; tie handling). |

### Written vs sounding

- **Default:** written `<pitch>`; `<transpose>` ignored.
- **`apply_sounding_transpose` / `--sounding-transpose`:** concert pitch; may respell via `spelled_note_from_chromatic_midi`.

### Other parser policies

- **Grace / cue notes:** optional inclusion (onset mode); grace often excluded in sounding mode (no duration).
- **Deduplication:** user-controlled (`dedupe_notes_by_midi`) — first occurrence kept per grid unit.
- **Ties, chords, voices, backup/forward, divisions:** handled per `iav.musicxml_io` algorithms — parser quality and exporter quirks (Sibelius, Dorico, MuseScore, etc.) affect extraction.

**MusicXML results are not performed audio.**

---

## 11. Manual input semantics

Accepted formats via `parse_manual_note_string` ([TECHNICAL_MANUAL.md §9](../TECHNICAL_MANUAL.md)):

- **C4**, **Eb5**, **C#4**, **F##3**, **C+4** (quarter-sharp with octave)
- **C**, **Eb** — default octave **4** (or legacy **Octave** column)
- Accidentals: `#`, `b`, `bb`, `+`, numeric alter strings where supported

Invalid rows produce **errors** from `normalize_manual_notes`; **hints** (duplicates, unusual octaves) are non-blocking.

Manual input is a **symbolic entry point**, not a score engraver or parser.

---

## 12. Vertical cardinality and interval homogeneity

**Vertical cardinality** (`iav.vertical_cardinality`) counts **symbolic note events** / unique pitch units / pitch classes per slice. It describes **thickness** of a verticality, **not** acoustic density.

| Fact | Implication |
|------|-------------|
| More notes ≠ lower or higher **H** automatically | **H** depends on **interval distribution**, not note count alone. |
| High cardinality can increase pairwise diversity | More pairs ⇒ more histogram bins possible. |
| Dyads | Exactly **one** pairwise interval ⇒ maximal concentration under dominance (trivial case). |
| Cross-cardinality comparison | Compare dyads, triads, and larger aggregates **with care** — cardinality affects pair count and support bins. |

Passage charts plot **H over time** and **vertical note count** side by side — interpret jointly.

---

## 13. Interpretation table

| Metric / concept | Measures | Does not measure | Main interpretive risk |
|------------------|----------|------------------|------------------------|
| **`pair_score`** | Concentration of **all** unordered pairwise absolute distances | Adjacent regularity; voice-leading; consonance | Equating high score with “simple harmony” |
| **`chain_score`** (adjacent) | Concentration of **sorted consecutive** gaps | Full pair cloud; score-order motion | Assuming score-order steps match sorted chain |
| **`weighted_linear_score`** / **`weighted_quadratic_score`** | Weighted pair concentration (local emphasis in sorted order) | Auditory masking; orchestration balance | Treating weights as perceptual salience |
| **`hybrid_score`** / hybrid **H** | Blend of adjacent + pairwise concentration | Automatic optimal balance | Presenting α as perceptually calibrated |
| **H** | Selected headline concentration (0–1) | Universal “homogeneity truth” | Comparing **H** across different headline modes or EDOs |
| **H_label** | Fixed band on **H** | Musicological style label | Over-reading band names as aesthetic judgement |
| **Dominance** | Max category share | Which category is musically “important” | Ignoring **which** interval dominates |
| **Entropy / evenness** | Spread of distance distribution | Homogeneity directly (high evenness ⇒ low entropy concentration) | Calling high evenness “homogeneous” |
| **Type concentration** | Diversity of **labeled** pair types | Pitch-class set class | Confusing with Forte interval vector |
| **Interval vector** (mod 12) | Pitch-class pair classes 1…6 | Absolute pairwise labels on spelled height | Applying to microtonal or non-12-EDO material |
| **Vertical cardinality** | Symbolic note thickness per slice | Loudness; registral spread | Inferring **H** from note count alone |
| **EDO / `bin_cents`** | Quantisation grid | Performance intonation | Changing grid without reporting it |
| **Written vs sounding** | Notated vs transposed concert pitch | Recording pitch | Mixing modes across corpus |
| **MusicXML verticality mode** | Time-sliced vs pooled sonorities | Phrase structure semantics | Using **aggregate** on long scores |
| **`auto_alpha` / α** | Blend parameter (optional size-dependent α) | Listener preference | Hidden α changes when note count changes |

---

## 14. Examples of interpretive distinctions

1. **Whole-tone aggregate** — adjacent gaps may be **regular** (equal steps in sorted order) while **pairwise** distances remain **diverse** → high `chain_score`, lower `pair_score`.

2. **Repeated interval pattern** — many pairs share one distance class → high **dominance** and high **`pair_score`** (under dominance method).

3. **Chromatic cluster** — identical semitone **adjacent** steps → `chain_score` ≈ 1; **not** perceptually consonant.

4. **Dyad** — one pairwise interval ⇒ **pair_score** = 1 under dominance (trivial concentration).

5. **Same cardinality, different diversity** — two four-note sonorities can differ sharply in `distance_counts` and **H**.

6. **EDO change** — 12-EDO vs 24-EDO can split or merge distance bins and alter labels.

7. **Transposing instruments** — written B♭ clarinet part vs concert pitch mode yields different note sets and **H**.

---

## 15. Relation to musicological use

These metrics may **support** (not replace) analysis of:

- intervallic **regularity** and **heterogeneity** within a sonority;
- **aggregate morphology** (cluster vs spread vs stacked seconds);
- **chordal spacing** patterns in sorted register;
- **interval-type dominance** (e.g. third-heavy vs fifth-heavy pair histograms);
- **sonority comparison** within a fixed preset (same EDO, headline, method);
- **vertical profile evolution** across a passage (slice **H**, **ΔH**, cardinality);
- **adjacent vs global** organisation (chain vs pair diagnostics);
- identifying **stable vs heterogeneous** intervallic fields in orchestral or piano textures.

**Use several views together** — `pair_score`, `chain_score`, weighted scores, `classification`, optional **IC evenness** ([TECHNICAL_MANUAL.md §12](../TECHNICAL_MANUAL.md)), and vertical cardinality — rather than a single scalar **H**.

---

## 16. Limitations

Explicit boundaries:

- No audio signal analysis; no spectral density; no timbral modelling.
- No loudness model; no acoustic roughness / sensory dissonance.
- No perceptual validation; no listener-response data.
- No automatic musicological labels beyond **heuristic** English strings.
- Results depend on: **parsing**, **EDO**, **binning**, **deduplication**, **MusicXML mode**, **transposition option**, **headline mode**, **homogeneity method**, and **thresholds**.
- The tool **supports** analysis; it does **not** replace score study, hearing, or contextual criticism.

---

## 17. Formula quick reference

All formulae below are **implementation-specific** (verified against `iav.interval_analysis_core._homogeneity`, `_edo_labels`, `_metrics_for_notes`, and [TECHNICAL_MANUAL.md §4](../TECHNICAL_MANUAL.md)). Natural logarithm (`math.log`) throughout.

### Pairwise count construction

For notes with units `U_i`, all unordered pairs `i < j`:

- `distance_counts[|U_i − U_j|] += 1`
- `interval_counts[label(|U_i − U_j|)] += 1`

### Adjacent count construction

Sort units: `U_1 ≤ … ≤ U_N`. For each `k = 1…N−1`:

- `adj_counts[U_{k+1} − U_k] += 1`

### Proximity weighting

Sorted units, indices `i < j`, distance `d = U_j − U_i`, weight `w = 1/(j−i)^p`:

- `weighted[d] += w` (float masses)

### Dominance

`Dominance = max(counts) / sum(counts)` (or max weight / sum weights).

### Support-bounded evenness

`Evenness_sup = min(1, H_ent / ln(support_bins))` with `support_bins = max(1, U_max − U_min + 1)`.

**Entropy concentration:** `score = 1 − Evenness_sup`.

### Type concentration

`1 − (K − 1)/(T − 1)` on labeled pair types (`T` total pairs, `K` distinct labels).

### Hybrid headline

`H = α · chain_score + (1 − α) · pair_score` (α clamped to [0, 1]).

### Combined consensus

`H_consensus = sqrt(max(0, H_dom) · max(0, H_ent))`.

### Interval-vector evenness (supplement)

`ic_evenness_from_notes` applies `entropy_evenness_counts` to **nonzero** entries of the Forte **interval vector** on unique 12-TET pitch classes — optional supplement in `iav.symbolic_profile`, **not** headline **H**.

---

## Document history

- **2026-06-07:** Initial metric semantics guide (documentation-only).
