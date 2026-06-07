# Interval Aggregate Analyzer — Technical Manual

**Version:** 2026-05-21 (rev. 2) — aligned with `iav.pitch_model`, `iav.musicxml_io`, `iav.interval_analysis_core` (intervallic headline modes), `iav.set_class_12tet`, **`iav/symbolic_profile`**, **`iav/vertical_cardinality`** (§7.8; no PC inference from unique-pitch count), **`iav/charts.py`** (passage timelines: **H** + vertical note count), **`iav/musicxml.py`** (slice summary + JSON), batch/canonical tooling, **`installers/`**, Streamlit (`iav.widgets*`, `pages/1_Which_metric_to_use.py`, `app.py`), root **shims**, and `tests/` (see `docs/ARCHITECTURE.md`, §10).  
**Scope:** This document specifies **intervallic homogeneity** on a declared EDO grid: how concentrated or diverse the **unordered pairwise interval multiset** is for a notated sonority (§4–§5). Analysis is **symbolic and score-based** (§1.3)—not audition, not psychoacoustics. **Registral dispersion** (register layout, density, banding) is **out of scope**; use a separate tool for that. Optional §12 adds mod-12 interval-class evenness and reference **interval** fingerprints only.

**Interpretive guide:** For musicological reading, what **H**, **pair_score**, **chain_score** (adjacent), proximity-weighted scores, dominance, entropy, and headline modes **mean and do not mean**, see **[docs/METRIC_SEMANTICS.md](docs/METRIC_SEMANTICS.md)** (formulas here remain authoritative for implementation).

**Math formatting:** Delimiters use **MathJax / KaTeX conventions** — inline `$…$`, display `$$…$$` — so the same source renders on **Stack Exchange**, many Markdown previews, and Jupyter. (Avoid legacy LaTeX `\$` / `\\[` delimiters when pasting; use `$` / `$$`.)

---

## Table of contents

1. [Conceptual model](#1-conceptual-model) (aggregate, stance §1.3, data flow §1.4)
2. [Pitch representation and quantization](#2-pitch-representation-and-quantization)
3. [Pairwise intervals and labels](#3-pairwise-intervals-and-labels)
4. [Homogeneity and related scores](#4-homogeneity-and-related-scores)
5. [Aggregate classification (heuristic labels)](#5-aggregate-classification-heuristic-labels) (dominance, evenness, stacking, H bands)
6. [12-TET pitch-class set theory](#6-12-tet-pitch-class-set-theory)
7. [MusicXML ingestion algorithms](#7-musicxml-ingestion-algorithms) (slice summary §7.6–7.8)
8. [Operational limits and UI-derived parameters](#8-operational-limits-and-ui-derived-parameters) (threshold modes, headline mode, α)
9. [Manual input validation and hints](#9-manual-input-validation-and-hints)
10. [Testing, regression, and batch tools](#10-testing-regression-and-batch-tools)
11. [Pedagogical tutorial](#11-pedagogical-tutorial) (12 lessons + checklist)
12. [Intervallic supplements and protocols](#12-intervallic-supplements-and-protocols) (§12.1–12.6)
13. [Related work (symbolic tools only)](#13-related-work-symbolic-tools-only)
14. [References](#14-references)
15. [Document history](#document-history)

---

## 1. Conceptual model

### 1.1 What is an “aggregate” here?

An **aggregate** is a **finite multiset of pitched notes**, each note represented as a **spelling triple** (also `NoteTuple` in code):

$$
n = (\text{letter}, a, o)
$$

where:

- `letter` ∈ {C, D, E, F, G, A, B} maps to a diatonic pitch-class index (see §2.1);
- $a \in \mathbb{R}$ is an alteration in **semitones** relative to the natural letter (e.g. `+1` for sharp, microtones allowed);
- $o \in \mathbb{Z}$ is the **octave number** as entered in the UI (same convention as MusicXML: see §2.2).

**Sonic height** used for intervals and homogeneity is always derived from this tuple via **`pitch_model.chromatic_midi_float`** (§2.2), then quantized (§2.4). For **MusicXML**, the app and CLI use **`parse_musicxml_upload`** (§7.1): by default the tuple follows **written** `<pitch>` (transpose tags ignored); with **Apply MusicXML transposition (concert pitch)** or **`--sounding-transpose`**, each measure’s `<transpose>` is applied and the tuple may be **respelled** to a sharp-leaning canonical form—not guaranteed to match the engraver’s written orthography.

### 1.2 What this tool is **not**

- **Not** voice-leading or spelling-aware: enharmonically equivalent pitch distances receive the **same** interval label when they collapse to the same grid step.
- **Not** a model of **spectral** or **perceptual** consonance—only discrete pitch-class distance on the selected grid.
- **Not** octave-equivalent by default: intervals compare **absolute** quantized pitches unless you explicitly interpret pitch-class sets (§6).

### 1.3 Epistemological stance (symbolic analysis only)

This project operates entirely in the domain of **notated pitch structure**:

- Inputs are **spellings and score times** (manual table or MusicXML), quantized on a declared EDO grid.
- Outputs are **interval histograms**, **homogeneity indices**, and optional **mod-12 interval-class** summaries—not registral dispersion maps.
- The tool does **not** model **audition**, **psychoacoustic consonance**, **roughness**, **timbral fusion**, or **listener preference**. UI language uses **intervallic homogeneity / interval heterogeneity**, not “consonant” or “how it sounds.”

**Registral span** appears only inside entropy **normalization** (§4.4 `support_bins`) and in a collapsed **auxiliary geometry** expander—not as a primary analytic product.

### 1.4 Application data flow (single aggregate)

1. **Input assembly** — manual table and/or MusicXML (`iav.note_sources`, `iav.musicxml`); optional dedupe (§2.5, §8.4).  
2. **Core metrics** — `metrics_for_notes` → **`AggregateHomogeneityMetrics`** (§4.9): pairwise/chain histograms, headline **$H$**, classification string.  
3. **Intervallic supplement** — `intervallic_profile_for_notes` (§12): optional mod-12 ic evenness and reference interval fingerprints.  
4. **Presentation** — `iav.results.render_aggregate_results` (tables, charts via `iav.charts`, CSV + **`vertical_cardinality_profile.json`** export); passage modes add a second timeline chart and the same JSON via `iav.musicxml` (§7.6–7.8).

MusicXML **multi-slice** modes build a per-slice table first, then optionally stop before step 3–4 on a single chosen slice (§7.3, §12.6).

---

## 2. Pitch representation and quantization

### 2.1 Letter to chromatic pitch-class (within octave)

Let $\mathrm{pc}(\text{letter})$ be:

| letter | C | D | E | F | G | A | B |
|--------|---|---|---|---|---|---|---|
| pc     | 0 | 2 | 4 | 5 | 7 | 9 | 11 |

### 2.2 Semitone height (12-TET float before grid quantization)

The implementation uses a **MIDI-like** semitone index with **middle C as 60**:

$$
s(n) = (o + 1) \cdot 12 + \mathrm{pc}(\text{letter}) + a .
$$

This matches `iav.pitch_model.chromatic_midi_float` (also re-exported on `interval_analysis` for backward compatibility); `note_to_units` multiplies that value by 100 and quantizes to the analysis grid.

### 2.3 Analysis grid: EDO and `bin_cents`

The UI offers EDO values $E \in \{12, 24, 48\}$. The step size in **cents** is:

$$
\Delta = \frac{1200}{E}, \qquad \texttt{bin\_cents} = \mathrm{round}(\Delta).
$$

For these three settings, $\texttt{bin\_cents} \in \{100, 50, 25\}$.

### 2.4 Cents and unit quantization

Define **cents** from semitone height:

$$
\mathrm{cents}(n) = 100 \cdot s(n).
$$

Define the **raw unit** (real-valued):

$$
u_{\mathrm{raw}}(n) = \frac{\mathrm{cents}(n)}{\texttt{bin\_cents}}.
$$

The **integer unit** $U(n)$ is obtained by **rounding to the nearest integer** using asymmetric floor rules (Python `quantize_units`):

$$
U(n) = \begin{cases}
\left\lfloor u_{\mathrm{raw}} + \tfrac{1}{2} \right\rfloor & u_{\mathrm{raw}} \ge 0,\\[4pt]
-\left\lfloor -u_{\mathrm{raw}} + \tfrac{1}{2} \right\rfloor & u_{\mathrm{raw}} < 0.
\end{cases}
$$

**Interpretation:** For $E=12$ ($\texttt{bin\_cents}=100$), one unit is one **12-TET semitone**. For finer EDOs, one unit is a smaller pitch step in cents.

### 2.5 Deduplication (“collapse to unique pitches”)

Given a list of notes, the app keeps the **first occurrence** of each distinct unit $U(n)$ when deduplication is enabled (`dedupe_notes_by_midi`). This is order-dependent.

### 2.6 Module `iav.pitch_model` (single source for height and MusicXML accidentals)

Canonical implementation: **`iav/pitch_model.py`**. The repository root file **`pitch_model.py`** is a thin **shim** that re-exports the same symbols for legacy imports.

- **`NOTE_BASE`**: letter → integer pc($\text{letter}$) as in §2.1.
- **`ACCIDENTAL_TOKENS`**: MusicXML `<accidental>` text (lowercased) → semitone offset, including quarter-sharp / quarter-flat etc.
- **`chromatic_midi_float(letter, alter, octave)`**: implements $s(n)$ in §2.2 (used by **`iav.interval_analysis_core.note_to_units`** and by **`iav.musicxml_io`** when building MIDI height from a note tuple—including after MusicXML transposition in the **`*_with_sounding_transpose`** parser variants; root shims **`interval_analysis`** / **`analysis_core`** expose the same entry points).
- **`spelled_note_from_chromatic_midi(total_midi)`**: inverse map used in **`iav.musicxml_io`** **only when** a note’s sounding height was shifted by a **non-zero** cumulative transpose in those **`*_with_sounding_transpose`** variants; emits a normalized `(letter, alter, octave)`; see §7.1. Not used by the primary (written-pitch-only) parser entry points.
- **`AnalyzedPitch`**: optional dataclass carrying `midi_semitones` plus optional spelling metadata (for API clarity; the Streamlit path still primarily uses `NoteTuple`).

`interval_analysis` re-exports **`chromatic_midi_float`** for backward compatibility.

---

## 3. Pairwise intervals and labels

### 3.1 Unordered pairs

For $N$ notes, the app iterates **all unordered pairs** using combinations (not permutations):


$$
\mathcal{P}_2 = \{ \{i,j\} : i<j \}, \qquad |\mathcal{P}_2| = \binom{N}{2}.
$$

For each pair $(n_i, n_j)$, let:


$$
\Delta U = \bigl| U(n_i) - U(n_j) \bigr|
$$

(the implementation orders by swapping so $\Delta U \ge 0$).

### 3.2 String labels (`interval_counts`)

- If $\texttt{bin\_cents} = 100$, $\Delta U$ is interpreted as a **non-negative semitone span** and labeled via a fixed **enharmonic simple-interval** map (quality + number) with octave extension (`semitone_to_label`). This is **pitch distance**, not Roman-numeral harmonic analysis.
- If $\texttt{bin\_cents} \neq 100$, the label is:


$$
\texttt{f"{}c"} = (\Delta U \cdot \texttt{bin\_cents}) \text{ formatted as integer cents}.
$$

### 3.3 Integer distance histogram (`distance_counts`)

The same $\Delta U$ values are also counted in a dictionary keyed by **integer** $\Delta U$ (not the string label).

---

## 4. Homogeneity and related scores

### 4.1 Chain (adjacent) intervals after sorting

Let $U_1 \le U_2 \le \cdots \le U_N$ be the sorted units (the code sorts $U(n)$ values).

Define adjacent gaps:


$$
g_k = U_{k+1} - U_k, \quad k = 1,\ldots,N-1.
$$

Histogram $A$ (`adj_counts`): for each integer gap $g$, count how many times it appears among $\{g_k\}$.

**Important:** This “chain” is **not** a voice-leading path in score order; it is the **melodic chain through sorted pitch height** for the current aggregate.

### 4.2 Dominance (maximum category share)

For a histogram with nonnegative integer counts $c_r$ over categories $r=1,\ldots,K$, total $T=\sum_r c_r$:


$$
\mathrm{Dominance} = \frac{\max_r c_r}{T}, \quad T>0.
$$

Applied separately to:

- **pairwise** distances (`distance_counts`);
- **chain** gaps (`adj_counts`).

### 4.3 Shannon entropy and normalized evenness

For counts $c_r$ with $T=\sum_r c_r$, probabilities $p_r = c_r/T$. Shannon entropy (natural logarithm, matching Python `math.log`):


$$
H = -\sum_{r: p_r>0} p_r \ln p_r.
$$

Let $K$ be the number of **observed** categories with nonzero count. For $K \ge 2$, let $H_{\max} = \ln K$. The implementation defines **`entropy_evenness`** on a count dictionary as:

$$
\mathrm{Evenness}_{\mathrm{norm}} =
\begin{cases}
0 & K \le 1 \quad\text{(including empty: defined as 0)},\\[6pt]
\dfrac{H}{H_{\max}} & K \ge 2.
\end{cases}
$$

**Rationale:** When only **one** category has positive count, $H = 0$ (no uncertainty). Treating evenness as **0** (not 1) makes **concentration** $1 - \mathrm{Evenness}_{\mathrm{norm}}$ equal **1** for that distribution—i.e. a single interval type is **maximally concentrated**, not maximally “even.”

**Edge:** empty dictionary ⇒ $0.0$ evenness (same as no diversity).

> **Pipeline note.** The **`entropy_evenness`** primitive defined here is used in the production pipeline **only** as a fallback in **`classify_aggregate`**, when no pairwise evenness is supplied by the caller. The principal entropy-concentration path used for **`homogeneity_score(method="entropy")`** and for the reported **`evenness_score`** applies a distinct **support-bounded** normalisation, defined in §4.4 below.

### 4.4 “Entropy concentration” subscores

For homogeneity with `method == "entropy"`, the code uses **`entropy_evenness_supportbounded`**, not **`entropy_evenness`** from §4.3.

**(a) Shannon entropy.** For counts $c_r$ with $T=\sum_r c_r$ and $p_r=c_r/T$, the same entropy as §4.3 applies:

$$
H(X) = -\sum_{r:\,p_r>0} p_r \ln p_r,
$$

with natural logarithm (Python `math.log`).

**(b) Support-bounded denominator.** Let $U_{\min}=\min_i U_i$ and $U_{\max}=\max_i U_i$ in **`note_to_units`** grid steps for the aggregate. Define **pitch span** $\mathrm{span}=U_{\max}-U_{\min}$ (integer in code: `pairwise_pitch_span_units`)—used only to set the entropy ceiling for **interval** histograms, not as a registral-dispersion score. Define

$$
\texttt{support\_bins} = \max(1,\,\mathrm{span}+1),
$$

matching **`pairwise_distance_support_bins`**. The normalising ceiling is

$$
H_{\mathrm{sup}} = \ln\bigl(\max(1,\,\texttt{support\_bins})\bigr),
$$

i.e. $\ln(\texttt{support\_bins})$ once $\texttt{support\_bins}\ge 2$; for $\texttt{support\_bins}=1$ the implementation returns evenness **0.0** without dividing by $\ln 1$.

Define **support-bounded evenness** on a histogram $X$ (counts $c_r$, same $H(X)$ as above):

$$
\mathrm{Evenness}_{\mathrm{sup}}(X) =
\begin{cases}
0 & \text{if }X\text{ is empty or }H_{\mathrm{sup}}\le 0,\\[6pt]
\min\!\left(1,\,\dfrac{H(X)}{H_{\mathrm{sup}}}\right) & \text{otherwise.}
\end{cases}
$$

**(c) Grid step and EDO.** One unit step is **`bin_cents`** cents of pitch height per `note_to_units` quantisation. Thus **12-EDO** (`bin\_cents=100`) yields one **semitone** per step; **24-EDO** (`bin\_cents=50`) yields one **quarter-tone** step; **48-EDO** (`bin\_cents=25`) yields one **eighth-tone** step (finer grids analogously).

**(d) Intra-aggregate consistency.** The **same** $\texttt{support\_bins}$ computed from the full aggregate is passed as the denominator reference for **both** the chain gap histogram $A$ (**`adj_counts`**) and the pairwise absolute-distance histogram $D$ (**`distance_counts`**), so pairwise and chain entropy subscores share one registral frame.

**(e) Edge cases.** An **empty** $A$ or $D$ yields subscore **0.0** (no contribution). If $\texttt{support\_bins}\le 1$ (in particular **$\mathrm{span}=0$**: all pitches collapse to one grid height), **$\mathrm{Evenness}_{\mathrm{sup}}=0$**, so **concentration** $1-\mathrm{Evenness}_{\mathrm{sup}}=1$—a trivially homogeneous aggregate is treated as **maximally concentrated**.

**(f) Rationale (design).** Support-bounded normalisation aims at **comparability across aggregates** that occupy similar registral extents but differ in how many distance categories appear. Classical **Pielou** normalisation by $\ln K$ (with $K$ the count of **observed** categories) would tie the ceiling to incidental category multiplicity rather than to the **fixed** number of absolute-distance bins induced by span.

**(g) Subscore formulae.** Let $A$ denote **`adj_counts`** and $D$ denote **`distance_counts`**. Then

$$
\text{chain\_score} = 1 - \mathrm{Evenness}_{\mathrm{sup}}(A), \qquad
\text{pair\_score} = 1 - \mathrm{Evenness}_{\mathrm{sup}}(D).
$$

With a **single** positive count in $A$ or $D$, $H=0$ so $\mathrm{Evenness}_{\mathrm{sup}}=0$ and the corresponding subscore is **1.0** (fully concentrated).

### 4.5 Intervallic metric suite and headline $H$

For each aggregate, **`homogeneity_score`** always computes **four** concentrations (dominance or entropy path, §4.4):

| Code field | Construction |
|------------|----------------|
| **`pair_score`** | Unordered absolute pairwise distances (**pairwise intervallic concentration**) |
| **`chain_score`** | Adjacent gaps after sorting by pitch height (**adjacent intervallic regularity**) |
| **`weighted_linear_score`** | All pairs weighted by $1/\|j-i\|$ |
| **`weighted_quadratic_score`** | All pairs weighted by $1/\|j-i\|^2$ |

**Headline $H$** follows **`IntervallicHeadlineMode`** (UI: *Headline intervallic metric*). Default: **`pairwise_intervallic_concentration`** ($H = S_{\mathrm{pair}}$). Other modes: adjacent ($H = S_{\mathrm{chain}}$); proximity-weighted linear or quadratic; **hybrid** $H = \alpha S_{\mathrm{chain}} + (1-\alpha) S_{\mathrm{pair}}$ with **`alpha_used`** (§8.3). API flag **`blend_chain_in_h=True`** maps to hybrid.

All four scores appear in the UI expander *Intervallic metric suite*; only the selected mode sets **`H`**, **`H_label`**, and slice **ΔH**. **Rationale:** chromatic clusters can have maximal adjacent regularity (repeated semitone steps) while the full pairwise cloud stays diverse—both views are analytically meaningful (§11.6).

### 4.5.1 Proximity-weighted pairs

After sorting pitch heights, pair $(i,j)$ with $i<j$ contributes weight $w_{ij} = 1/(j-i)^p$ ($p=1$ linear, $p=2$ quadratic) to the histogram bin of $|u_j - u_i|$. Concentration is computed on these **float** masses via **`dominance_weighted`** / **`entropy_evenness_supportbounded_weighted`**.

### 4.6 Combined mode consensus

When `homogeneity_method == "combined"`, the app computes headline **$H$** twice (dominance and entropy paths), each respecting the selected **`IntervallicHeadlineMode`** (§4.5), and defines:


$$
H_{\mathrm{consensus}} = \sqrt{\max(0, H_{\mathrm{dom}})\cdot \max(0, H_{\mathrm{ent}})}.
$$

This is the **geometric mean** of the two $H$ values (after clamping negatives to zero inside the square root). In combined mode, the value shown as primary **$H$** in **`metrics_for_notes`** is **`H_consensus`**; dominance-only and entropy-only headline values are retained as **`H_dom`** / **`H_ent`**.

### 4.7 Cluster compactness (separate descriptive metric)

Let $U_{\min} = \min_i U_i$, $U_{\max} = \max_i U_i$, span $S = U_{\max}-U_{\min}$.

For $N\ge 2$ and $S>0$, let $\mathcal{P}_2(U)$ be all unordered pairs of **units**:


$$
\overline{d} = \frac{1}{\binom{N}{2}} \sum_{i<j} |U_i - U_j|.
$$

Define:

$$
C = 1 - \frac{\overline{d}}{S}.
$$

The UI reports $C$ as **cluster compactness** (described in the app as a **custom** geometric summary), and also reports pitch span and average distance in **cents** by scaling $S$ and $\overline{d}$ by `bin_cents`.

Edge cases:

- $N<2$: returns compactness $1.0$ with zero span.
- $S=0$: returns compactness $1.0$.

### 4.8 Type concentration on **labeled** pairwise intervals

Let pairwise string labels have counts; total $T=\sum$ counts, $K$ distinct labels.


$$
\mathrm{TypeConcentration} =
\begin{cases}
0 & T=0,\\
1 & T\le 1,\\
1 - \dfrac{K-1}{T-1} & \text{otherwise.}
\end{cases}
$$
(This is **`type_concentration`**, a **custom** index on labeled pairwise interval types, not a textbook “diversity” measure.)

### 4.9 `metrics_for_notes` and `AggregateHomogeneityMetrics`

`metrics_for_notes` returns a frozen dataclass **`AggregateHomogeneityMetrics`** (`iav/aggregate_metrics.py`). Mapping access (`m["H"]`, `"key" in m`) is supported for tests and legacy callers.

**Core scores**

| Field | Meaning |
|-------|---------|
| **`H`** | Headline homogeneity for the selected **method** and **`intervallic_headline_mode`** (§4.5); in **combined** mode, **`H_consensus`**. |
| **`chain_score`**, **`pair_score`** | $S_{\mathrm{chain}}$, $S_{\mathrm{pair}}$ for the active method (dominance or entropy). |
| **`weighted_linear_score`**, **`weighted_quadratic_score`** | Proximity-weighted concentrations ($p=1$, $p=2$); always computed; headline only if that mode is selected. |
| **`intervallic_headline_mode`** | **`IntervallicHeadlineMode`** enum value used for **$H$** (§4.5). |
| **`alpha_used`** | Blend weight when mode is **hybrid** (§8.3); logged otherwise but does not change **$H$** unless hybrid. |
| **`H_dom`**, **`chain_dom`**, **`pair_dom`** | Dominance-path subscores (combined mode only; else mirrored or `None` per method). |
| **`H_ent`**, **`chain_ent`**, **`pair_ent`** | Entropy-concentration path (combined or entropy mode). |
| **`H_consensus`** | Geometric mean (combined mode only). |
| **`evenness_score`** | $\mathrm{Evenness}_{\mathrm{sup}}(D)$ on **`distance_counts`** (§4.4); **0.0** if no pairs. |
| **`pairwise_entropy_support_bins`** | $\texttt{support\_bins}=\max(1,\mathrm{span}+1)$ used for entropy subscores. |
| **`blend_chain_in_h`** | **Deprecated flag:** `True` iff headline mode is **hybrid** (API compat); prefer **`intervallic_headline_mode`**. |
| **`H_label`** | Categorical band from **`h_band_label(H)`** (§5.3). |
| **`classification`** | Full heuristic string from **`classify_aggregate`** (§5). |
| **`type_score`** | **`type_concentration`** on labeled intervals (§4.8). |
| **`compactness_score`**, **`pitch_span`**, **`avg_distance`** | Cluster compactness (§4.7), span and mean distance in cents. |
| **`interval_counts`**, **`distance_counts`**, **`adj_counts`** | Histograms for export / charts. |
| **`top_pair_*`**, **`top_chain_*`** | Dominant distance / gap label and share. |

**Display metadata (UI / CSV)**

- **`H_primary_title`**, **`H_primary_help`**: main homogeneity line; help mentions pairwise-default vs blend when relevant.
- **`pair_metric_title`**, **`chain_metric_title`**, **`evenness_title`**: component labels; evenness describes support-bounded Shannon on **`distance_counts`**.

The **`entropy_evenness`** / $\ln K$ primitive (§4.3) is **not** the source of **`evenness_score`**; it remains the **`classify_aggregate`** fallback when **`pairwise_abs_evenness`** is omitted (§5).

**UI wording.** Headline **$H$** is labeled **intervallic homogeneity**; **interval heterogeneity** $= 1 - H$.

**Intervallic profile (separate dataclass).** `intervallic_profile_for_notes` returns **`IntervallicProfile`** (`iav/symbolic_profile.py`; aliases `SymbolicProfile` / `symbolic_profile_for_notes` for compatibility). Not embedded in **`AggregateHomogeneityMetrics`**.

---

## 5. Aggregate classification (heuristic labels)

The **`classify_aggregate`** function builds a **semicolon-separated** English summary. **`metrics_for_notes`** also sets **`H_label`** via **`h_band_label`** (§5.3), which is **independent** of this string.

### 5.1 Pairwise interval dominance and evenness

Let the top **labeled** pairwise interval $\ell^\*$ have count $c^\*$, with total pairwise intervals $T$ from **`interval_counts`**.

- **Dominance share:** $\rho = c^\*/T$.
- If $\rho \ge$ **`dominance_threshold`**: segment **`{ℓ*}-dominant`**; else **`no dominant interval`**.

**Evenness band** uses $\mathrm{E}$ = evenness input:

- When called from **`metrics_for_notes`**, **`pairwise_abs_evenness`** = **`evenness_score`** = $\mathrm{Evenness}_{\mathrm{sup}}(D)$ on **`distance_counts`** (§4.4)—**not** **`entropy_evenness`** on labeled strings.
- If **`pairwise_abs_evenness`** is **`None`**, fallback **`entropy_evenness(interval_counts)`** (§4.3). Not used in the main UI pipeline.

Thresholds **`even_high`**, **`even_low`** (§8.2):

- **`high evenness`** if $\mathrm{E} \ge \texttt{even\_high}$;
- **`low evenness`** if $\mathrm{E} \le \texttt{even\_low}$;
- **`mid evenness`** otherwise.

### 5.2 Chain / stacking regularity (sorted-pitch chain)

Let **`chain_dominance`** be **`chain_score`** from the same homogeneity **method** as the classification context (dominance share of adjacent gaps, or entropy concentration, depending on mode).

| Condition | Suffix appended |
|-----------|-----------------|
| **`chain_dominance` $\ge 0.95$** | `; uniform stacking` |
| **`chain_dominance` $\ge$ `chain_threshold`** and **$< 0.95$** | `; predominantly regular stacking` |
| else | `; irregular stacking` |

Default **`chain_threshold`** = **0.60** (user-tunable in Standard mode; fixed in §8.2).

**Example (12-EDO).** Five chromatic semitones in one octave (C, C♯, D, D♯, E with distinct spellings) yield identical adjacent gaps after sorting → **`chain_score` = 1.0** → **`uniform stacking`**, even when the pairwise histogram lists many interval classes.

### 5.3 Intervallic homogeneity band labels (`h_band_label`)

Applied to headline **$H$** (or **`H_consensus`** in combined mode). Fixed thresholds (not user sliders):

| $H$ | **`H_label`** |
|-----|----------------|
| $H \ge 0.80$ | `homogeneous` |
| $0.50 \le H < 0.80$ | `moderately homogeneous` |
| $0.20 \le H < 0.50$ | `moderately heterogeneous` |
| $H < 0.20$ | `heterogeneous` |

### 5.4 Full label shape

$$
\texttt{classification} = \underbrace{\text{dominant-interval clause}}_{\S5.1}
;\ \underbrace{\text{evenness clause}}_{\S5.1}
\ \underbrace{\text{stacking clause}}_{\S5.2}.
$$

Empty **`interval_counts`** ⇒ **`no intervals`**.

---

## 6. 12-TET pitch-class set theory

This block is only available when **every** note maps to an **integer** semitone grid (no residual microtone after rounding) so that pitch classes in $\mathbb{Z}_{12}$ are well-defined (`pitch_classes_12tet_unique`).

### 6.1 Pitch class

For integer-semitone MIDI-like index $s$:


$$
\mathrm{PC}(s) = s \bmod 12 \in \{0,\ldots,11\}.
$$

### 6.2 Interval vector (Forte)

For distinct pitch classes $\{p_i\}$, for each unordered pair $i<j$:


$$
d = (p_j - p_i) \bmod 12, \qquad
\mathrm{ic} = \min(d, 12-d) \in \{0,\ldots,6\}.
$$

The vector $\langle n_1,\ldots,n_6\rangle$ counts pairs with $\mathrm{ic} \in \{1,\ldots,6\}$. (Interval class 0 is not included in the 6-slot vector.)

### 6.3 Prime form (implemented Forte-style search)

The code:

1. Takes the sorted set of pitch classes mod 12.
2. For each inversion flag (original vs $p \mapsto -p \pmod{12}$), and each transposition $t \in \{0,\ldots,11\}$, forms the translated set, rotates it to start at its minimum element as pitch class 0, and collects candidate tuples.
3. Returns the **lexicographically smallest** candidate tuple (`prime_form_12tet`).

This matches a common pedagogical “Forte prime form” procedure; different textbooks may differ in tie-breaking for pathological sets—always cite **this implementation** for reproducibility.

### 6.4 Normal order (compact rotation)

`normal_order_12tet` embeds sorted pitch classes twice (duplicated with +12) and scans length-$N$ windows to minimize the linear span $w_N - w_1$; ties break by lexicographic comparison of the transposed window starting at 0.

---

## 7. MusicXML ingestion algorithms

Parsing uses **defusedxml** and tag suffix matching (namespace-agnostic). **Compressed** `.mxl` files are constrained:

- at most **2000** zip members;
- total uncompressed size at most **20 MiB**.

### 7.1 Pitch from a `<note>` element

- Reads `<pitch><step>`, `<octave>`, optional `<alter>`.
- If `<alter>` is missing, may read `<accidental>` text mapped through `pitch_model.ACCIDENTAL_TOKENS` (including quarter-tones).
- Invalid `<alter>` text with no valid accidental ⇒ note skipped and **`skipped_microtonal`** incremented (implementation detail).

**Written pitch vs sounding transpose (two API surfaces)**

The package exposes **six** MusicXML parser entry points (three “written pitch only”, three “apply `<transpose>`”). The Streamlit app and batch CLI route through **`parse_musicxml_upload`** (`iav/musicxml_io/_dispatch.py`): by default the **written-pitch** trio; when **Apply MusicXML transposition (concert pitch)** is enabled (or CLI **`--sounding-transpose`**), the **transpose** trio is used instead.

1. **Primary (written `<pitch>` only):** `parse_musicxml_bytes`, `parse_musicxml_verticalities_bytes`, `parse_musicxml_sounding_verticalities_bytes`. Cumulative `<attributes><transpose>` is **not** read; the per-note offset into `extract_pitch_from_note` is always **0**. Leftover `<transpose>` tags are **harmless** for pitch import. Use this when the written score is already the pitch set you want to analyse.

2. **Concert pitch (`*_with_sounding_transpose` or dispatch with `apply_sounding_transpose=True`):** `parse_musicxml_bytes_with_sounding_transpose`, `parse_musicxml_verticalities_bytes_with_sounding_transpose`, `parse_musicxml_sounding_verticalities_bytes_with_sounding_transpose`. Each updates a running transpose from each measure’s `<attributes>` when present:


$$
\Delta_{\mathrm{transpose}} = \text{chromatic} + 12\cdot \text{octave-change}.
$$

When $\Delta_{\mathrm{transpose}} \neq 0$ for a note, sounding MIDI is computed and mapped back to a **canonical sharp-leaning** `(step, alter, octave)` via `pitch_model.spelled_note_from_chromatic_midi`. That keeps interval arithmetic aligned with **sounding** pitch per MusicXML semantics but **does not preserve** the engraver’s written orthography for the same height.

### 7.2 Timing in quarter-note space

`<divisions>` per quarter note: if $D$ is divisions, a duration of $\texttt{dur}$ divisions is:


$$
\Delta t = \frac{\texttt{dur}}{D} \quad \text{(quarter notes)}.
$$

`backup` and `forward` move a per-voice cursor in the same units.

### 7.3 Onset verticalities (`parse_musicxml_verticalities_bytes`)

For each voice (or `_global` if absent):

- Maintain `voice_time` and a **global** `cursor_time` for the default voice bucket.
- Onset of a non-chord note advances to `measure_offset + voice_time[voice]`.
- Chord tones share the **last onset** for that voice (`last_onset`).
- After a non-chord note, `voice_time` advances by $\Delta t$.
- **Measure offset** advances by $\max_v \text{voice\_time}[v]$ after scanning the measure.

Notes with ties that are **stop/continue without start** may be excluded from slices (`tie_stop_only` logic) to avoid double counting continuation notes (see code).

### 7.4 Sounding verticalities (`parse_musicxml_sounding_verticalities_bytes`)

For notes with duration $>0$, the algorithm emits **+1** / **−1** events at start/end of sustained pitch, merging ties by extending an open interval keyed by `(part_id, staff, voice, note_tuple)`.

Between consecutive event times $t_k < t_{k+1}$, the active multiset of sounding notes defines a slice $[t_k, t_{k+1})$.

### 7.5 Validation assets (`validation/fixtures`, `validation/corpus`)

- **`validation/fixtures/`**: small XML files tied to unit tests (ties, grace notes, transpose, etc.).
- **`validation/corpus/`**: additional **synthetic** scores (multi-voice, `backup`/`forward`, double-flat style) documented in that folder’s `README.md`. Tests in `tests/test_corpus_musicxml.py` run the three MusicXML parsers on **every** `*.xml` in both directories to catch regressions.

This is **not** a substitute for a large corpus of real exports from multiple notation programs; extending `validation/corpus/` is the intended place for new stress files.

### 7.6 MusicXML slice summary (passage profile over time)

When import mode is **onset** or **sounding verticalities** and slice mode is **All slices (summary)** or **Time window (summary)**, the app (`iav/musicxml.py`) builds a **passage profile**:

1. Filter slices by **minimum notes per slice** and skip slices with fewer than 2 notes or more than **`MAX_NOTES`** (500).
2. For each remaining slice, call **`metrics_for_notes`** with the user’s homogeneity method, thresholds, and **`intervallic_headline_mode`** (§8.3).
3. Append optional columns from **`slice_intervallic_columns`** (§12.4): `PC cardinality`, `IC evenness (mod 12)` when defined.
4. Apply **`passage_delta_rows`**: column **`ΔH (prev slice)`** = headline **$H$** minus the previous row’s **$H$** (score-time order; not registral dispersion).

**UI outputs (in order):**

- **Altair line chart (intervallic homogeneity)** — **`chart_homogeneity_over_time`** (`iav/charts.py`): headline **$H$** (Y, 0–1) vs **`Time (quarters)`** (X, quarter-note units from MusicXML `<motion>` / divisions). Requires **at least two** slices; points are labelled in the tooltip with slice index, time label, note count, and **`H label`**.
- **Altair line chart (vertical cardinality)** — **`chart_vertical_cardinality_over_time`** (`iav/charts.py`): **one** plotted series — **`vertical_note_count`** (Y) vs **`Time (quarters)`** (X). Shown whenever the passage summary is built; works from **one or more** slices with valid **`Notes`**. Tooltips may show **`Unique pitches`** and **`PC cardinality`** when those CSV columns exist; they are **not** separate plotted lines (§7.8). Title **Vertical Note Count over Time** (or **Vertical Cardinality Profile over Time** when any row has **`Unique pitches`**). This is **not** acoustic density, loudness, or spectral mass.
- **Summary table** — all columns below.
- **`slice_summary.csv`** download.
- **`vertical_cardinality_profile.json`** download — time series of vertical cardinality metrics aligned with the same slices (§7.8).

**Single slice** mode skips the summary and charts; it analyses one chosen verticality like a normal aggregate (§1.4).

**Typical columns in the table / CSV**

| Column | Meaning |
|--------|---------|
| **`Slice`** | Row index in the filtered list (1-based). |
| **`Time`** | Display label: onset time (`0.000`) or sounding interval (`1.500-2.250`). |
| **`Time (quarters)`** | Numeric X-axis for the chart: onset time, or **start** of a sounding slice. |
| **`Notes`** | Vertical note count in the slice (after optional dedupe); equals **`vertical_note_count`** in JSON (§7.8). |
| **`Unique pitches`** | Optional: distinct pitch units on the selected EDO grid (from **`enrich_slice_summary_row`**). |
| **`PC cardinality`** | Optional (12-EDO, integral spellings): distinct pitch classes mod 12; set by **`enrich_slice_summary_row`** and/or **`slice_intervallic_columns`** when computable. |
| **Headline H column** | Name depends on homogeneity method, e.g. `H (interval dominance)`, `H (consensus)`, `H (interval entropy concentration)`. |
| **`Pairwise …` / `Chain …`** | Component scores for the same method. |
| **`Interval evenness (span-norm.)`** | §4.4 on pairwise distance histogram. |
| **`Label`**, **`H label`** | §5 classification string and §5.3 band. |
| **`ΔH (prev slice)`** | Stepwise change in headline **$H$**. |

**What the passage profile is not:** it does **not** pool all slices into one interval histogram, nor compute a duration-weighted mean **$H$** over the window (unless you derive that from the CSV externally). Each slice is one **simultaneous verticality** at a score time.

**Worked use case (dense orchestral page):** onset verticalities + **Time window** on an active excerpt; low **$H$** on 6–8 note attacks and **$H=1$** on 2-note slices often alternate (cluster vs isolated interval)—see slice table and chart together.

### 7.7 Aggregate import warning (many notes)

If import mode is **Aggregate (all notes)** and the parsed list has **more than 50** pitches, the UI warns (`iav/musicxml.py`) that **all notes are treated as one verticality with no time slicing**. **Collapse to unique pitches** only removes duplicate **heights**; it does **not** restore temporal structure. For passages, movements, or full pages, use **§7.6** verticality modes instead.

### 7.8 Vertical symbolic cardinality (passage and aggregate)

**Vertical cardinality** describes how many notated pitch **events**, **distinct pitch units**, and (when defined) **pitch classes** are present in each vertical slice. It is a **structural / notational** thickness measure — orthogonal to intervallic homogeneity **$H$** (§4–§5). It does **not** measure acoustic density, loudness, perceptual fusion, or registral dispersion.

**Implementation:** `iav/vertical_cardinality.py` (metrics, JSON builder, row enrichment); charts in **`iav/charts.py`**; passage UI wiring in **`iav/musicxml.py`**; manual/aggregate JSON in **`iav/results.py`**.

**Per-slice metrics** (after the same dedupe policy as homogeneity analysis):

| Field | Meaning |
|-------|---------|
| **`vertical_note_count`** | Count of notes/events in the slice (matches **`Notes`** in `slice_summary.csv`). |
| **`vertical_unique_pitch_count`** | Distinct quantized pitch units (`note_to_units` on the active EDO grid). |
| **`vertical_pitch_class_cardinality`** | Distinct pitch classes mod 12 when **EDO = 12** and every note maps to an integral chromatic step; otherwise omitted (`null` in JSON). |

**Code paths (do not conflate):**

| Function | Role |
|----------|------|
| **`vertical_cardinality_for_notes`** | Ground truth from the prepared note list (used when building each slice row and in aggregate mode). |
| **`enrich_slice_summary_row`** | Writes **`Notes`**, **`Unique pitches`**, **`PC cardinality`** into `slice_summary.csv` from the same notes analysed for **$H$**. |
| **`vertical_cardinality_from_summary_row`** | Rebuilds JSON series fields from an existing summary row. **`vertical_pitch_class_cardinality`** is read **only** from **`PC cardinality`**; it is **never** inferred from **`Unique pitches`** or **`Notes`** (octave doublings such as C4+C5 → two units, one pitch class). |
| **`build_vertical_cardinality_profile`** | Assembles the full JSON document and **`summary_statistics`** (statistics use **`vertical_note_count`** only). |

**JSON export (`vertical_cardinality_profile.json`):**

- **`schema_version`:** `"1.0"`
- **`metric_family`:** `"vertical_cardinality"`
- **`source`:** `input_file`, `analysis_mode` (`onset_verticalities` \| `sounding_verticalities` \| `manual`), `deduplication_active`, `edo`
- **`definitions`:** prose for the three metrics above
- **`time_unit`:** `"quarters"`
- **`series`:** one object per analysed slice (`slice_index`, `time_quarters`, `vertical_note_count`, `vertical_unique_pitch_count`, `vertical_pitch_class_cardinality`). The last two may be JSON **`null`** when not recoverable from the row.
- **`summary_statistics`:** `n_slices`, min/max/mean/median (and `std_vertical_note_count`) over **`vertical_note_count`** only (not over unique-pitch or pitch-class fields).

**Temporal modes:** built from the same slice loop as §7.6 via **`enrich_slice_summary_row`** then **`build_vertical_cardinality_series`**. JSON **`vertical_note_count`** matches **`Notes`** row-for-row. **`vertical_unique_pitch_count`** and **`vertical_pitch_class_cardinality`** match CSV columns when present; otherwise JSON uses the rules in **`vertical_cardinality_from_summary_row`** (see below).

**Manual / aggregate mode (no timeline):** one series entry at **`time_quarters`: 0.0** with all three fields from **`vertical_cardinality_for_notes`** on the prepared aggregate; download appears in the **Export** section with **`interval_analysis.csv`**.

**Population rules for `vertical_cardinality_from_summary_row`:**

| CSV / row input | JSON output field |
|-----------------|-------------------|
| **`Notes`** present | **`vertical_note_count`** (integer) |
| **`Notes`** missing / invalid | **`vertical_note_count`**: `null` |
| **`Unique pitches`** present | **`vertical_unique_pitch_count`** |
| **`Unique pitches`** missing | **`vertical_unique_pitch_count`** defaults to **`vertical_note_count`** if **`Notes`** is valid (event count proxy only — not pitch-unit analysis) |
| **`PC cardinality`** present | **`vertical_pitch_class_cardinality`** |
| **`PC cardinality`** missing | **`vertical_pitch_class_cardinality`**: **`null`** always (no inference from unique-pitch count; regression: `tests/test_vertical_cardinality.py`) |

**Chart vs table vs JSON:** the passage chart plots **`vertical_note_count`** only; the summary table and JSON carry optional unique-pitch and pitch-class columns when the slice pipeline computed them.

**Defensive behaviour:** empty slices are skipped by the existing §7.6 filters; missing or non-numeric **`Notes`** are omitted from the cardinality chart dataframe; repeated **`time_quarters`** values are preserved (table order = score order).

---

## 8. Operational limits and UI-derived parameters

### 8.1 Note count cap

`MAX_NOTES = 500`: pairwise analysis requires $\binom{N}{2}$ pairs—this cap protects runtime.

### 8.2 Analysis threshold modes (`AnalysisThresholdMode`)

The UI offers two modes for classification thresholds (§5.1–5.2):

| Mode | Behaviour |
|------|-----------|
| **Standard** | User sliders: **`dominance_threshold`**, **`even_high`**, **`even_low`**, **`chain_threshold`**. |
| **Fixed thresholds (heuristic)** | Presets: **`dominance_threshold` = 0.60**, **`even_high` = 0.80**, **`even_low` = 0.30**, **`chain_threshold` = 0.60**. |

Fixed mode is for **comparable yardsticks** across sessions without tuning sliders. Headline **$H$** bands (§5.3) are **always** fixed at 0.80 / 0.50 / 0.20 regardless of this mode.

### 8.3 Headline intervallic mode and hybrid α (`compute_alpha_used`)

**UI:** radio *Headline intervallic metric* maps to **`IntervallicHeadlineMode`** (`iav/analysis_enums.py`, `iav/widgets_analysis_section.py`):

| Mode | Headline **$H$** |
|------|------------------|
| **`pairwise_intervallic_concentration`** (default) | $S_{\mathrm{pair}}$ |
| **`intervallic_adjacency_regularity`** | $S_{\mathrm{chain}}$ |
| **`proximity_weighted_linear`** / **`proximity_weighted_quadratic`** | Weighted concentrations (§4.5) |
| **`hybrid_intervallic_homogeneity`** | $\alpha_{\mathrm{used}} S_{\mathrm{chain}} + (1-\alpha_{\mathrm{used}}) S_{\mathrm{pair}}$ |

The **Intervallic metric suite** expander always shows all four constructions plus the active headline. Sidebar page **`Which metric to use?`** (`pages/1_Which_metric_to_use.py`, `iav/metric_guide_content.py`) explains when to pick each mode.

**API:** `homogeneity_score(..., intervallic_headline_mode=...)`; **`blend_chain_in_h=True`** is equivalent to **hybrid** with the supplied α.

**`compute_alpha_used`** applies **only** when headline mode is **hybrid** **and** *Auto-adjust α* is enabled. Let $N$ be note count, $n_{\mathrm{adj}} = \max(1, N-1)$.

If auto-adjust is on, $N\ge 3$, and $n_{\mathrm{adj}}\ge 2$:

$$
\alpha_{\mathrm{used}}
= \alpha_{\mathrm{base}}
+ (1-\alpha_{\mathrm{base}})\cdot
\frac{n_{\mathrm{adj}}-1}{(n_{\mathrm{adj}}-1)+k_{\mathrm{auto}}}.
$$

Otherwise $\alpha_{\mathrm{used}} = \alpha_{\mathrm{base}}$.

For non-hybrid modes, **`alpha_used`** is still stored on **`AggregateHomogeneityMetrics`** for CSV reproducibility but **does not change** headline **$H$**.

### 8.4 Forced deduplication on large uploads

If duplicates are **not** manually collapsed but the note list length $\ge 200$ (`FORCE_DEDUPE_THRESHOLD`), the app **forces** deduplication with a warning.

### 8.5 Development install and automated tests

The project is configured as an installable package (`pyproject.toml`). Recommended local setup from the repository root:

```bash
pip install -e ".[dev]"
pytest
```

`[tool.pytest.ini_options]` sets `testpaths = ["tests"]` and `pythonpath = ["."]` so **`iav`**, **`pitch_model`**, **`analysis_core`**, and **`interval_analysis`** resolve when running **`pytest`** from the repository root (without requiring `PYTHONPATH=.`).

---

## 9. Manual input validation and hints

### 9.1 `parse_note_name` and `parse_manual_note_string`

- **`parse_note_name`**: pitch class only (C, Eb, C+); **rejects** `C4`-style strings (digits would be read as accidentals). Used internally and in reference-sonority JSON.
- **`parse_manual_note_string`**: table entry (`C4`, `Eb5`, `C#3`) or pitch class with **`default_octave`** (default **4**). Accidentals: **`ACC_TO_SEMITONES`** in `_edo_labels.py`.

### 9.2 `normalize_manual_notes`

- Coerces Streamlit / pandas table rows to a list of dicts (`_coerce_manual_table_rows`); missing **pandas** yields a narrow `ImportError` path (no broad silent swallow).
- **Blank Note rows** are skipped silently (placeholder rows from the data editor do not produce errors).
- Each non-blank **Note** cell is parsed with **`parse_manual_note_string`** (legacy rows may still supply a separate **Octave** column as default only).

### 9.4 Manual table widget (`iav.widgets_manual_section`)

The Streamlit **`st.data_editor`** stores its state in **`st.session_state["manual_notes_table"]`**. A fresh empty `DataFrame` must **not** be passed on every rerun (that resets user input). The widget uses `key="manual_notes_editor"`, `hide_index=True`, and a single **Note** column (e.g. `C4`, `Eb5`, `F#3`). **`parse_manual_note_string`** splits spelling and register; pitch without a trailing digit defaults to octave **4**. Legacy tables with a separate **Octave** column are merged on load. With **`num_rows="dynamic"`**, Streamlit may add a **checkbox column** for bulk row delete (UI-only).

### 9.3 `manual_input_hints` (non-blocking)

- Emits **hints** (warnings in the UI) for: **duplicate** parsed pitches across rows; **octaves outside about 1–8** as “unusual” for concert scores.
- Hints do **not** replace validation from §9.2.

---

## 10. Testing, regression, and batch tools

### 10.1 Automated tests (`tests/`)

- **Pytest** from the repository root (`pip install -e ".[dev]"` recommended). **`pythonpath = ["."]`** in `pyproject.toml` resolves **`iav`** and root shims without an install.
- **MusicXML smoke:** `tests/test_corpus_musicxml.py` — every file under `validation/fixtures/` and `validation/corpus/` must parse.
- **Methodology / classification:** `test_pairwise_methodology.py`, `test_classification_chain_and_h_band.py`, `test_intervallic_headline_modes.py`.
- **Symbolic profile:** `test_symbolic_profile.py` (reference catalog, ic evenness, passage deltas).
- **Backward-compat shims:** `tests/test_backward_compat_shims.py`.
- **Optional music21:** `tests/test_music21_interval_vector.py` (skipped if `music21` not installed).

### 10.2 Canonical sonority corpus (frozen metrics)

- **Data:** `iav/data/canonical_sonorities.json` — 13 labelled sonorities with expected **`pair_score`**, **`chain_score`**, headline **$H$**, etc., for default UI settings.
- **Loader:** `iav/canonical_corpus.py`; **tests:** `tests/test_canonical_sonorities.py`.
- **Regenerate expectations** after intentional metric changes: `python scripts/generate_canonical_expectations.py`.
- **Example inputs:** `examples/corpus/*.json` (see `examples/corpus/README.md`).

### 10.3 Canonical MusicXML corpus

- **Scores:** `validation/canonical/*.xml` (five minimal scores: aggregate, verticalities, ties, transpose, grace).
- **Frozen expectations:** `iav/data/canonical_musicxml.json`; **builder:** `python scripts/build_canonical_musicxml.py`; **tests:** `tests/test_canonical_musicxml.py`.

### 10.4 Batch CLI (no Streamlit)

```bash
python analyze_corpus.py --input examples/corpus --output results/
python analyze_corpus.py --verify-canonical -i examples/corpus -o results/
```

Equivalent after `pip install -e .`: **`iav-analyze`** (`iav/cli.py`, `iav/batch_analyze.py`). Writes `results.csv`, `results.json`, `config_used.json`, `log.txt`, `summary_statistics.csv`.

### 10.5 Sensitivity and annotated pilot

- **α / threshold sweeps:** `python scripts/sensitivity_report.py` → `docs/reports/`; notebook `notebooks/sensitivity_report.ipynb`.
- **Human-label pilot:** `examples/annotated_corpus/manifest.json` + `python scripts/run_annotated_study.py` → `docs/reports/annotated_pilot/` (`iav/annotated_study.py`).

### 10.6 Continuous integration

GitHub Actions (`.github/workflows/ci.yml`): **pytest**, **ruff check**, **ruff format --check**, **mypy** on `iav`, canonical sonority + MusicXML verify, batch smoke on `examples/corpus/`, sensitivity report, annotated pilot, optional music21 job (Python 3.10–3.11).

### 10.7 Other validation assets

- **Reference sonorities (UI fingerprints):** `iav/data/reference_sonorities.json` (not the same file as the canonical regression corpus).
- **Ad-hoc XML:** `validation/fixtures/`, `validation/corpus/` (§7.5).

Executable tests and frozen JSON are authoritative when this manual and the code disagree.

---

## 11. Pedagogical tutorial

This section is a **guided course** for analysts working on **late-Romantic through contemporary orchestral** sonorities: dense verticals, doublings, microtonal notation, and MusicXML exports from different engraving tools. Each lesson states a **learning goal**, **steps in the app**, **what to observe**, and a **takeaway**. Cross-references point to formal definitions earlier in this manual.

**Prerequisites:** Run the app (`streamlit run app.py`). For a shorter UI-only guide, see [QUICK_GUIDE.md](QUICK_GUIDE.md).

**Recommended path:** Lessons 1–3 (pitch grid) → 4–5 (reading scores) → 6–8 (homogeneity) → 9–10 (special topics). Lesson 11 is a capstone checklist.

---

### 11.1 Lesson 1 — From spellings to analysis “units”

**Goal:** Separate **notated pitch** from **interval tallies** on a chosen grid.

**Concept.** The software does not hear the orchestra; it places each note on an EDO lattice (§2) and counts **unordered** distances (§3).

**Exercise.**

1. Manual table: **C4**, **E4**, **G4**, **C5** in the **Note** column (§9.1); or **C**, **E**, **G**, **C** with default octave 4 for the first three.
2. EDO **12** (`bin_cents = 100`).
3. Open interval counts: expect **M3**, **P5**, **P8** (and enharmonic duplicates collapsed in labels).

**Observe.** Doubling the top **C** after enabling “collapse duplicates” does not add new interval *types*—only multiplicities if dedupe is off (§2.5).

**Takeaway.** You are measuring **absolute pitch-distance structure**, not tonal function, voice-leading, or orchestration timbre.

---

### 11.2 Lesson 2 — Pairwise “cloud” vs sorted “chain”

**Goal:** Understand why the app reports **two** regularity views—and why headline **$H$** defaults to pairwise only (§4.5).

**Concept.** After sorting pitches by height, the **chain** counts steps between neighbours (§4.1). **Pairwise** counts all $\binom{N}{2}$ spans (§3).

**Exercise A — regular chain, rich pairwise set.**

1. Notes: **C4, E4, G4, B4, D5** (major-third stack).
2. Homogeneity: **Dominance**; headline mode **Pairwise intervallic concentration** (default).
3. Compare **`chain_score`** (high: one adjacent gap repeats) vs **`pair_score`** (lower: many interval classes in the full cloud). Switch headline to **Intervallic adjacency regularity** to make **$H$** follow the chain.

**Exercise B — chromatic cluster.**

1. Five consecutive semitones in one register (e.g. **C, C#, D, D#, E** at octave 4).
2. Read **`classification`**: expect **`uniform stacking`** (§5.2) while pairwise types remain diverse.

**Optional.** Choose **Hybrid intervallic homogeneity** and set $\alpha \approx 0.7$: headline **$H$** blends chain and pairwise (§4.5.1, §8.3).

**Takeaway.** A passage can look **regular as a scale fragment** in register yet **heterogeneous as a chord** under pairwise statistics—common in XX–XXI orchestral writing (clusters vs tertian voicings).

---

### 11.3 Lesson 3 — EDO and microtonal scores

**Goal:** Choose a grid that preserves notated microtones.

**Exercise.**

1. Enter **C+** (quarter-sharp) at octave 4 per manual accidental table (§9).
2. Compare EDO **12** vs **24** vs **48**: watch labels switch between semitone names and `Nc` cent strings (§3.2).
3. If the note rounds to the same unit as **C** natural on a coarse grid, the microtone **vanishes**—that is a quantization artefact, not “the composer intended a natural”.

**Takeaway.** For **quarter-tone** orchestral parts (many post-1945 scores), prefer **24-EDO** or **48-EDO**; keep **12-EDO** for standard semitone notation.

---

### 11.4 Lesson 4 — MusicXML: three time models

**Goal:** Pick an import mode that matches your analytical question.

| Question you ask | Mode |
|------------------|------|
| “What pitch classes / intervals appear in this excerpt overall?” | **Aggregate** |
| “What harmony attacks at each metric moment?” | **Onset verticalities** |
| “What pitch sets are **sounding** between two times?” | **Sounding verticalities** |

**Exercise.**

1. Use a short **chordal** excerpt (8–20 bars), not a full opera score, in **onset verticalities**.
2. Set **minimum notes per slice** to 3–4 to drop single-line moments.
3. Choose **Time window (summary)** and restrict to one active page or passage (quarter-note slider).
4. Inspect the **H-over-time chart**, the **vertical note-count chart**, **`slice_summary.csv`**, and **`vertical_cardinality_profile.json`**: multi-note slices vs 2-note slices often show **low vs high H** under dominance (§7.6); cardinality tracks **how thick** each verticality is in note count (§7.8).
5. Toggle **grace notes** once: see how ornamental attacks enter or leave slices (§7.3).

**Transpose warning.** By default the GUI reads **written** `<pitch>` (§7.1). For transposing instruments, enable **Apply MusicXML transposition (concert pitch)** in **MusicXML upload**, or use batch **`--sounding-transpose`** / `parse_musicxml_upload(..., apply_sounding_transpose=True)`.

**Takeaway.** Verticality modes are **time-aware** performance of harmony; aggregate mode is a **bag of pitches**—valid for a single sonority, misleading for an entire movement without slicing (§7.7).

---

### 11.5 Lesson 5 — Doublings and orchestral chords

**Goal:** Use deduplication the way a score analyst would.

**Concept.** Orchestral chords often double roots and fifths at the unison or octave. Interval **histograms** can overweight doublings unless you collapse identical grid heights (§2.5).

**Exercise.**

1. Enter a **four-note** chord, then duplicate **C** and **G** at the same octave without dedupe: pairwise counts inflate.
2. Enable **Collapse to unique pitches**: counts reflect **set of sounding heights**, not **number of staves**.

**Takeaway.** For **harmonic set** questions, dedupe **on**; for **texture / doubling weight** questions, dedupe **off** and interpret counts as weighted.

---

### 11.6 Lesson 6 — Reading intervallic homogeneity output

**Goal:** Interpret **`H`**, **`H_label`**, **`evenness_score`**, **`classification`**, and optional **Intervallic context** (§12).

**Fields (see §4.9, §5, §12).**

- **`H`**: **intervallic homogeneity** (pairwise interval concentration by default).
- **`H_label`**: coarse band (`homogeneous` … `heterogeneous`) at fixed cutoffs 0.80 / 0.50 / 0.20 (§5.3).
- **`evenness_score`**: spread of the pairwise **distance** histogram (§4.4).
- **`classification`**: dominant interval + evenness + stacking suffix (§5).
- **`IntervallicProfile`**: optional ic evenness and reference interval L1 matches (§12).

**Exercise.**

1. **C major triad** (C–E–G): note high **`pair_score`** under dominance; check reference match to **major_triad_closed**.
2. **Whole-tone tetrachord**: compare pairwise distance table with mod-12 interval vector in **Intervallic context**.

**Takeaway.** This tool measures **interval content homogeneity**, not registral dispersion.

---

### 11.7 Lesson 7 — Dominance vs entropy vs combined

**Goal:** Pick an **intervallic homogeneity** method aligned with your question.

| Method | Emphasizes | When it helps |
|--------|------------|----------------|
| **Dominance** | Largest share of one distance | Clear “winner” interval (e.g. many **P5**s in open fifths) |
| **Entropy concentration** | Whole histogram vs span ceiling | Many interval types, no single winner (dense mixed intervals) |
| **Combined** | Agreement of both | Sanity check; **`H_consensus`** is geometric mean (§4.6) |

**Exercise.** Same sonority under all three homogeneity **methods**; keep headline mode on **pairwise**. Note when **combined** consensus is low because dominance and entropy **disagree**—that is informative, not a bug.

**Takeaway.** Method choice is **epistemic**, not “more correct”; document which you used.

---

### 11.8 Lesson 8 — Threshold modes and labeling

**Goal:** Use **Standard** vs **Fixed** thresholds (§8.2) deliberately.

**Exercise.**

1. **Standard:** lower **`dominance_threshold`** until a sparse sonority becomes `{interval}-dominant`.
2. **Fixed (0.60 / 0.80 / 0.30):** rerun the same notes; compare **`classification`** only (headline **$H$** bands unchanged).

**Takeaway.** Fixed mode supports **comparable labels** across a study; Standard mode supports **sensitivity analysis**.

---

### 11.9 Lesson 9 — Pitch-class set tools (12-TET)

**Goal:** Relate **register-specific** distances to **mod-12** set structure (§6).

**Exercise.**

1. Whole-tone collection: **C4, D4, E4, F#4** (integer semitones).
2. Inspect interval vector / prime form when the UI offers §6 tools.
3. Add a **quarter-sharp** note on 12-EDO without integral semitone: §6 tools should **not** apply.

**Takeaway.** Forte-style summaries answer **“what set is this modulo 12?”**; pairwise lists answer **“what intervals appear in this orchestration register?”**—orthogonal questions for much XX–XXI music.

---

### 11.10 Lesson 10 — Worked comparison (two sonorities)

**Goal:** Integrate lessons 2, 6, and 7 in one table-friendly comparison.

**Setup (12-EDO, dedupe on, entropy method, blend off, fixed thresholds).**

| Sonority | Notes (oct 4 unless noted) | Expect (qualitatively) |
|----------|----------------------------|-------------------------|
| **A** Chromatic run | C, C#, D, D#, E | High **`chain_score`**, `uniform stacking`; moderate/low pairwise **`H`** |
| **B** Open fifths | C2, G2, D3, A3 | Lower chain regularity; stronger fifth presence in pairwise dominance |

**Steps.** Enter A, export or note **`H`**, **`classification`**, **`evenness_score`**. Clear table; enter B; repeat.

**Discussion prompt.** Which sonority is “more homogeneous”? The answer **depends on the statistic**—pairwise **$H$** vs chain suffix vs your musical question. That ambiguity is why the manual separates §4.5 (headline **$H$**) from §5.2 (stacking clause).

---

### 11.11 Capstone checklist

Before citing results in a paper, lesson plan, or orchestration critique, confirm:

1. **EDO** matches the notation (12 / 24 / 48).
2. **Dedupe** matches intent (harmonic set vs weighted texture).
3. **MusicXML mode** matches time scope (aggregate vs slice).
4. **Written pitch** vs transpose policy is documented (§7.1).
5. **Homogeneity method** and **headline intervallic mode** (and hybrid **α** if used) are stated.
6. **Threshold mode** (Standard vs Fixed) is stated for **`classification`**.
7. **Intervallic supplements** (references, ic evenness) cited when used (§12).
8. Numbers are described as **symbolic heuristics**, not perceptual consonance (§1.2–1.3).

---

### 11.12 Further reading inside this project

- [QUICK_GUIDE.md](QUICK_GUIDE.md) — UI control reference for non-specialists.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — module map and release hygiene.
- `tests/test_pairwise_methodology.py`, `tests/test_classification_chain_and_h_band.py` — §4.5, §5.
- `tests/test_symbolic_profile.py` — §12.
- [QUICK_GUIDE.md](QUICK_GUIDE.md) — UI; [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — modules.

---

## 12. Intervallic supplements and protocols

**Module:** `iav/symbolic_profile.py`  
**Reference data:** `iav/data/reference_sonorities.json`  
**Tests:** `tests/test_symbolic_profile.py`, `tests/test_manual_table_coercion.py` (§9.4)

This section does **not** implement registral dispersion. It only adds **intervallic** context beyond headline **$H$**.

### 12.1 `IntervallicProfile` dataclass

Returned by **`intervallic_profile_for_notes(notes, *, edo, distance_counts)`**.

| Field | Meaning |
|-------|---------|
| `ic_evenness` | Pielou-style evenness on **observed** ic1–ic6 counts from the Forte interval vector (§6), when defined. |
| `ic_cardinality` | Number of distinct pitch classes mod 12. |
| `reference_comparisons` | Up to four `(ref_id, label, L1)` best matches vs catalog (§12.3). |

Aliases: **`SymbolicProfile`**, **`symbolic_profile_for_notes`** (backward compatibility).

### 12.2 IC evenness (`ic_evenness_from_notes`)

Distinct from **`evenness_score`** in §4.4: ic evenness summarises **mod-12 interval-class** variety; **`evenness_score`** summarises **absolute pairwise distance** variety with span-bounded normalization. Compare them when asking whether a sonority is ic-rich but interval-distance-concentrated, or the reverse.

### 12.3 Reference interval fingerprints (`compare_to_references`)

Catalog entries in `reference_sonorities.json` specify `label`, `notes` (parsed via **`parse_note_name`** for spellings like `Eb`), and `edo`.

For the target sonority, normalize **`distance_counts`** to shares $p(d)$. For each catalog sonority, build $q(d)$ the same way. **L1** $= \sum_d |p(d)-q(d)|$. Lower L1 ⇒ closer **pairwise interval profile** on the same EDO grid.

Shipped models: major/minor triad, dominant seventh, whole-tone tetrachord, chromatic cluster (5), open fifths, quartal stack.

### 12.4 Passage helpers (`iav/symbolic_profile.py`, `iav/charts.py`, `iav/vertical_cardinality.py`)

- **`slice_intervallic_columns`** — optional `PC cardinality`, `IC evenness (mod 12)` per slice row.  
- **`passage_delta_rows`** — **`ΔH (prev slice)`** only (§7.6).  
- **`vertical_cardinality_for_notes`** — cardinality from a note list (aggregate and slice ground truth).  
- **`enrich_slice_summary_row`** — sets **`Notes`**, **`Unique pitches`**, and **`PC cardinality`** on each summary row.  
- **`vertical_cardinality_from_summary_row`** — JSON field recovery from a row; **no** PC inference from unique-pitch count (§7.8).  
- **`build_vertical_cardinality_series`**, **`build_vertical_cardinality_profile`**, **`vertical_cardinality_profile_json`** — JSON export (§7.8).  
- **`homogeneity_timeline_dataframe`** — chart-ready rows for headline **$H$** vs time.  
- **`vertical_cardinality_timeline_dataframe`** — chart-ready rows for **`Notes`** / **`vertical_note_count`** vs time.  
- **`parse_slice_time_quarters`** — parses numeric time or labels like `2.125` / `1.5-2.25` (midpoint for ranges).  
- **`chart_homogeneity_over_time`** — Altair line + points (requires ≥2 slices).  
- **`chart_vertical_cardinality_over_time`** — Altair line + points for vertical thickness (≥1 valid slice).

### 12.5 UI (`iav.results`, `iav.widgets_analysis_section`)

- **Headline intervallic metric** — selects which concentration becomes **$H$** (§8.3); default pairwise.  
- **Intervallic metric suite** (expander) — all four constructions side by side.  
- **Intervallic homogeneity (headline H)** — primary numeric result (§4.5).  
- **Intervallic context (optional)** — ic vector / ic evenness + reference L1 list.  
- **Auxiliary geometry** (collapsed) — span and compactness; not intervallic homogeneity.  
- **Which metric to use?** — Streamlit sidebar page (`pages/1_Which_metric_to_use.py`) with decision guidance (`iav/metric_guide_content.py`).  
- **Passage timeline charts** — intervallic **$H$** and **vertical note count** in MusicXML **All slices** / **Time window** modes (§7.6–7.8); not shown for **Single slice** passage mode. Aggregate/manual analysis exports cardinality JSON only (§7.8).

### 12.6 Recommended protocols

**A — Sonority interval fingerprint:** one aggregate; read pairwise tables, **$H$**, classification, reference L1.  
**B — Passage interval profile:** **Verticalities** or **Sounding verticalities** + **Time window**; read **H-over-time chart**, **vertical cardinality chart**, **`slice_summary.csv`**, **`vertical_cardinality_profile.json`**, and **ΔH** (§7.6–7.8). Do **not** use **Aggregate** for long excerpts.  
**C — Mod-12 cross-check (12-EDO):** compare interval vector with pairwise distance histogram.

---

## 13. Related work (symbolic tools only)

| Tool / tradition | Overlap | Deliberate difference |
|------------------|---------|------------------------|
| **music21** | Intervals, chords, scores | General toolkit; does not ship this aggregate homogeneity + slice workflow. |
| **CRIM Intervals** | MusicXML intervals | Voice- and pattern-oriented; not multiset registral homogeneity. |
| **Humdrum `iv`** | Interval-class vectors | Score grammar; not registral distance concentration. |
| **PC-set calculators / musicxml-to-pcs** | Forte vector, prime form | Mod-12 only; not register-specific pairwise clouds. |
| **This analyzer** | Intervallic homogeneity on aggregates | Pairwise interval concentration heuristics; optional ic vector + reference fingerprints. |

No claim is made that this list is exhaustive; it anchors **symbolic** neighbours only (no MIR or psychoacoustic systems).

---

## 14. References

- **MusicXML** timing and pitch conventions: see the MusicXML specification (divisions, transpose, tie notations).
- **Pitch-class set theory / Forte**: introductory texts on atonal set theory (interval vector, prime form) — use this manual for **exact** algorithmic tie-breaks used here.
- **Shannon entropy:** standard information-theoretic $H$ (§4.3). **`entropy_evenness`** applies **Pielou-style** normalisation by $\ln K$ ($K$ observed categories with positive count; §4.3). **`entropy_evenness_supportbounded`** normalises by $\ln(\max(1,\texttt{support\_bins}))$ with $\texttt{support\_bins}=\max(1,\mathrm{span}+1)$ from registral extent (§4.4). The **production** entropy-concentration path and reported **`evenness_score`** use the **support-bounded** variant; **`entropy_evenness`** remains for the **`classify_aggregate`** fallback when no pairwise evenness is injected.
- **Intervallic supplements (§12):** ic evenness, L1 reference interval fingerprints; registral dispersion metrics removed from scope.

---

## Document history

- **2026-04-04:** Initial comprehensive manual generated to match the implementation in repository.
- **2026-04-21:** Updated for `pitch_model` (§2.2, §2.6, §7.1), corrected singleton behavior in **`entropy_evenness`** (§4.3–4.4), manual input and hints (§9), corpus/fixture testing (§7.5, §10), metrics display metadata (§4.9), heuristic framing (§1, §4.5–4.8), dev install / pytest (§8.4), and tutorial renumbering (§11). **MusicXML:** primary parsers read written pitch only; `*_with_sounding_transpose` variants cover regression / scripting (§7.1, `README.md`).
- **2026-04-21 (repo hygiene / tests):** `iav/note_sources.py` holds manual/XML merge logic without importing Streamlit; chart smoke tests skip if `altair` / `pandas` are missing; root `.gitignore` added for `__pycache__`, `.pytest_cache`, and `*.docx`.
- **2026-04-21 (API cleanup):** Removed the boolean `ignore_transpose` parameter from the primary parser signatures; added explicit `*_with_sounding_transpose` entry points; `scripts/clean_repo.ps1` and `docs/ARCHITECTURE.md` added.
- **2026-05-05:** Documentation alignment to executable code: §4.3 pipeline note; §4.4 rewritten for **`entropy_evenness_supportbounded`** and $\ln(\max(1,\texttt{support\_bins}))$ with $\texttt{support\_bins}=\max(1,\mathrm{span}+1)$; §4.9, §5, and §12 updated so entropy concentration and reported **`evenness_score`** match the support-bounded production path (not classical $\ln K$ on observed categories). **No executable code was modified.**
- **2026-05-18:** §4.5–4.5.1 (**`blend_chain_in_h`**, pairwise-default headline **$H$**); §4.6 combined-mode note; §4.9 **`AggregateHomogeneityMetrics`** field table; §5 restructured (stacking suffixes, **`h_band_label`** §5.3); §8.2–8.3 threshold modes and alpha scope; §11 expanded pedagogical tutorial (lessons 1–12). Matches `homogeneity_score`, `metrics_for_notes`, and UI defaults in `iav/widgets_analysis_section.py`.
- **2026-05-18 (symbolic profile + manual sync):** First **`iav/symbolic_profile.py`** drop; §1.3–1.4, §7.6, §12–§13; manual table session-state fix (§9.4).
- **2026-05-19:** Scope refocused on **intervallic homogeneity** only; removed register bands, registral density, and registral-vs-ic commentary from code and UI; §12 rewritten; manual input persists via `st.session_state["manual_notes_table"]`; blank Note rows skipped in **`normalize_manual_notes`**.
- **2026-05-20:** Full doc sync with reproducibility release: **`IntervallicHeadlineMode`** suite (§4.5, §4.9, §8.3); single-column manual **`C4`** notation (§9, §11.1); §10 expanded (canonical JSON/MusicXML, batch CLI, sensitivity, annotated pilot, CI); metric guide page (§12.5); tutorial headline-mode exercises (§11.2, §11.7).
- **2026-05-21:** §7.6–7.7 passage profile (**`chart_homogeneity_over_time`**, **`slice_summary.csv`**, aggregate warning); §12.4–12.6; §11.4 passage workflow; **`installers/`** documented in README and ARCHITECTURE.
- **2026-05-22:** Documentation and defaults aligned: preset ①–④ (**`iav/analysis_presets.py`**, **`ANALYSIS_PRESET.md`**); headline **H** default **pairwise** (not hybrid α=0.55); **`parse_musicxml_upload`** + UI **Apply MusicXML transposition (concert pitch)** + CLI **`--sounding-transpose`**; regression tests **`test_preset_default_metrics`**, **`test_musicxml_dispatch`**; removed obsolete nested-repo sync script.
- **2026-05-21 (vertical cardinality profile):** §7.8 vertical symbolic cardinality; second passage chart **`chart_vertical_cardinality_over_time`**; **`vertical_cardinality_profile.json`**; module **`iav/vertical_cardinality.py`**; tests **`tests/test_vertical_cardinality.py`**. Intervallic **$H$** definitions unchanged.
- **2026-05-21 (rev. 2 — PC cardinality export):** **`vertical_cardinality_from_summary_row`** no longer infers pitch-class cardinality from unique-pitch count; §7.8 documents chart (single Y-series), JSON population rules, and code-path table; tests **`test_pc_cardinality_not_inferred_when_column_missing`**, **`test_c4_c5_octave_duplicate_pitch_class_from_notes_not_inferred_in_json_row`**.
