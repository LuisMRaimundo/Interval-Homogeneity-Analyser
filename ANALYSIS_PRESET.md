# Fixed analysis preset (interface wording)

This page lists **exact control labels** as shown in the Streamlit app. Use the same homogeneity block for every example so results stay comparable.

## In the app

Open **Analysis presets** at the top of the main page:

1. Under **What are you analysing?**, choose **①–④** (see labels in the app).
2. Click **Apply preset now**, or enable **Automatically apply selected preset** so settings update when you change the preset.

The button writes the values below into the same controls listed in Parts 1–2.

**Headline idea:** one comparable **pairwise** intervallic concentration **H** per aggregate, with **Dominance (max share)** and **Fixed thresholds (heuristic)**. Adjacent regularity and hybrid blends are **diagnostic** (metric suite), not the default headline.

**Your two numbers after analysis**

| Read on the main results page | Meaning |
|------------------------------|---------|
| Value under **Intervallic homogeneity (headline H)** (title: **Pairwise intervallic concentration (headline H)**) | **Homogeneity** **H** (0–1) |
| **Interval heterogeneity (1 − H)** | **Heterogeneity** |
| **H label** in the summary (e.g. `moderately homogeneous`) | Fixed band label |

Do **not** use **All slices (summary)** or **Time window (summary)** when you need **one** H per example (those modes produce many values in `slice_summary.csv`).

### Model choices (read before disputing a number)

| Choice | Preset default | If you need something else |
|--------|----------------|----------------------------|
| Headline **H** | **Pairwise intervallic concentration** | **Hybrid** or **Adjacent** under *Headline intervallic metric (H)* — report α or say “adjacent regularity” |
| Scoring | **Dominance (max share)** | **Entropy concentration** if the full interval distribution should matter |
| Pitches | **Collapse to unique pitches** on | Uncheck for doublings / orchestral density |
| MusicXML pitch | **Written** `<pitch>` (default) | Check **Apply MusicXML transposition (concert pitch)** for transposing instruments |
| Interval labels | Chromatic **pitch-distance** bins | Not spelling-aware (e.g. tritone vs diminished fifth) |

**Example (chromatic cluster, dominance, preset defaults):** pairwise concentration ≈ **0.333**, adjacent regularity ≈ **1.000**, headline **H** ≈ **0.333** (not hybrid 0.700). Compare aggregates using the **same** headline mode and scoring.

---

## Shared settings (use for both parts below)

Open the main page and set the following **before** you load notes or MusicXML.

### Data preparation

| Control | Setting |
|---------|---------|
| **Collapse to unique pitches (selected EDO grid)** | **Checked** |

### Analysis mode

| Control | Setting |
|---------|---------|
| **Tuning system (EDO)** | **12** (use **24** or **48** only if the score uses quarter-tones or finer; see **Accidental reference** caption in **Manual input**) |
| **Choose a mode** | **Fixed thresholds (heuristic)** |

When **Fixed thresholds (heuristic)** is selected, the app shows:

> Fixed-threshold mode uses dominance ≥ 0.60, evenness ≥ 0.80 (high) and ≤ 0.30 (low).

You do **not** open **Labeling settings** in this mode.

### MusicXML (when you upload a file)

| Control | Setting |
|---------|---------|
| **Apply MusicXML transposition (concert pitch)** | **Unchecked** (written pitch). Check only for transposing-instrument scores analysed at **sounding** height. |

### Homogeneity model settings

| Control | Setting |
|---------|---------|
| **Homogeneity scoring** | **Dominance (max share)** |
| **Headline intervallic metric (H)** | **Global pairwise concentration (default)** |
| **α — weight on adjacent in hybrid H** | **0.55** (inactive unless you switch headline to **Hybrid**) |
| **Auto-adjust α with note count (hybrid only)** | **Unchecked** |
| **Auto-adjust strength (k)** | Leave at **4** (inactive while auto-adjust is off) |

**What this does (one line):**  
Headline **H** = **pairwise dominance** (share of the most frequent unordered pitch-distance type in the multiset). Open **Intervallic metric suite** for adjacent regularity, entropy paths, proximity-weighted scores, and optional hybrid with **α**.

---

## Part 1 — One vertical chord (manual input)

**Goal:** One chord typed by hand → **one** **H** and **Interval heterogeneity (1 − H)** on the results page.

### Steps

1. Leave **MusicXML upload** closed (do not upload a file).
2. Open **Manual input**.
3. In the table, column **Note**, enter **one note per row** (e.g. `C4`, `E4`, `G4`, `B4`). Use the spelling you want analysed.
4. Apply **Shared settings** (above).
5. Wait until the app analyses the note list (at least **2** notes required).
6. Scroll to **Intervallic homogeneity (headline H)**.

### Read your values

| On screen | Your homogeneity / heterogeneity |
|-----------|----------------------------------|
| **Pairwise intervallic concentration (headline H):** *0.xxx* (*xx.x*/100) | **H** = homogeneity |
| **Interval heterogeneity (1 − H):** *xx.x*/100 | heterogeneity |
| **H label** (in the classification summary above or beside metrics) | e.g. `homogeneous`, `moderately homogeneous`, … |

### Do not use for Part 1

- **MusicXML upload** / **Import mode**
- **Verticality analysis**
- Downloading **slice_summary.csv** or passage timeline charts (only in slice summary modes)

**Do use (Part 1):** after analysis, **Export** → **`vertical_cardinality_profile.json`** (single slice at time 0; same note count as the aggregate table).

---

## Part 2 — One vertical chord inside a MusicXML fragment

**Goal:** Same **Shared settings**, but pitches come from a score excerpt. You still get **one** **H** by analysing **one slice** only.

### Steps

1. Open **MusicXML upload** and use **Upload MusicXML (.xml, .musicxml, .mxl)**.
2. Set **Import mode** according to how the chord sounds in the score:

   | Situation | **Import mode** |
   |-----------|-----------------|
   | Chord at **attacks** (usual orchestral vertical) | **Verticalities (onset slices)** |
   | Chord **held** with ties / long durations | **Sounding verticalities** |

3. Set:

   | Control | Setting |
   |---------|---------|
   | **Minimum notes per slice** | **2** (or **3** if you want to drop two-note dyads) |
   | **Include grace notes (onset verticalities only)** | **Unchecked** |
   | **Include cue notes (onset verticalities only)** | **Unchecked** |
   | **Verticality analysis** | **Single slice** |
   | **Include manual notes in analysis** | **Unchecked** (unless you deliberately merge manual notes) |

4. Apply **Shared settings** (same as Part 1).
5. In **Choose slice to analyze**, pick the slice that matches your chord (check time and note count in the label, e.g. `3: t=4.250 (n=6)`).
6. If the app shows an editable pitch table for that slice, confirm pitches, then run analysis.
7. Scroll to **Intervallic homogeneity (headline H)** — same readings as Part 1.

### Read your values

Same as Part 1:

- **Pairwise intervallic concentration (headline H):** → **H**
- **Interval heterogeneity (1 − H):** → heterogeneity
- **H label** → band label

### MusicXML fragment — special case (entire excerpt = one sonority)

Use this **only** if the whole fragment should be **one** chord (all notes in the file belong to that verticality):

| Control | Setting |
|---------|---------|
| **Import mode** | **Aggregate (all notes)** |
| **Verticality analysis** | *(not used)* |

Then apply **Shared settings** and read **Intervallic homogeneity (headline H)** as above.

If the file has **more than 50** notes, the app warns that **Aggregate (all notes)** treats all pitches as one verticality with no time slicing — trim the XML to the chord first.

### Do not use for “one H per chord” in Part 2

| Control | Why |
|---------|-----|
| **All slices (summary)** | Many rows in **slice_summary.csv**, many H values |
| **Time window (summary)** | Same — one H per slice, not one per fragment |

Use those only when you study **change over time**, not for a single chord value.

---

## Part 3 — Active movement fragment (passage over time)

**Goal:** Many chords in an active excerpt → **H per slice**, **H-over-time chart**, **vertical note-count chart**, **`slice_summary.csv`**, and **`vertical_cardinality_profile.json`** (not one H for the whole fragment).

### Steps

1. Open **MusicXML upload** and use **Upload MusicXML (.xml, .musicxml, .mxl)** (trim the file to the passage when possible).
2. In **Analysis presets**, choose **④ Passage with many chords — H changes over time** and click **Apply preset now** (or enable **Automatically apply selected preset**).
3. Confirm these controls (preset sets them for you):

   | Control | Setting |
   |---------|---------|
   | **Import mode** | **Verticalities (onset slices)** |
   | **Minimum notes per slice** | **3** |
   | **Include grace notes (onset verticalities only)** | **Unchecked** |
   | **Include cue notes (onset verticalities only)** | **Unchecked** |
   | **Verticality analysis** | **Time window (summary)** |
   | **Include manual notes in analysis** | **Unchecked** |

4. Apply **Shared settings** (same homogeneity block as Parts 1–2).
5. Set **Select time window (quarter units)** to the active bars (e.g. one score page).
6. Read **Slice summary (intervallic homogeneity over time)**:
   - **Intervallic homogeneity across time** (chart)
   - **Vertical note count over time** (chart; symbolic thickness, not acoustic density)
   - Summary table
   - Download **`slice_summary.csv`** and **`vertical_cardinality_profile.json`**

### Read your values

| Output | Meaning |
|--------|---------|
| Column **`H (interval dominance)`** (each row) | **H** for that slice (pairwise dominance path when preset scoring is dominance) |
| **`ΔH (prev slice)`** | Change in headline **H** vs previous slice |
| **`H label`** (per row) | Band per slice |
| **`Notes`** | Vertical note count after dedupe (matches JSON **`vertical_note_count`**) |
| **`Unique pitches`** / **`PC cardinality`** | Optional in CSV when computed (12-EDO integral spellings for PC) |
| Mean/median of **H** in Excel | Optional **summary** for the whole window (you compute it) |
| **`vertical_cardinality_profile.json`** | Time series: `vertical_note_count`, optional unique-pitch and pitch-class fields; summary stats on note count only. **`vertical_pitch_class_cardinality`** is `null` in JSON if **PC cardinality** is missing from the row (not guessed from unique pitches) |

### Sustained harmony in the same fragment

If ties and **held** chords matter more than attacks only, after applying the preset change only:

| Control | Change to |
|---------|-----------|
| **Import mode** | **Sounding verticalities** |

Keep **Time window (summary)** and the **Shared settings**.

---

## Quick comparison

| | Part 1 — Manual | Part 2 — One chord (XML) | Part 3 — Active fragment |
|--|-----------------|--------------------------|---------------------------|
| Input | **Manual input** → **Note** | **MusicXML upload** + **Single slice** | **MusicXML** + **Time window (summary)** |
| **Import mode** | — | **Verticalities** or **Sounding verticalities** | **Verticalities (onset slices)** (default) |
| Homogeneity block | **Shared settings** | **Shared settings** | **Shared settings** |
| Output | One **H** + cardinality JSON | One **H** | Many **H** + charts + **slice_summary.csv** + **vertical_cardinality_profile.json** |

---

## Methods sentence (copy-paste)

*Pitch aggregates were analysed in 12-TET with **Collapse to unique pitches (selected EDO grid)** enabled, **Fixed thresholds (heuristic)**, **Homogeneity scoring** set to **Dominance (max share)**, and **Headline intervallic metric (H)** set to **Global pairwise concentration (default)** with **Auto-adjust α with note count (hybrid only)** off. Manual sonorities used **Manual input**; isolated verticalities used **Verticalities (onset slices)** or **Sounding verticalities** with **Verticality analysis** = **Single slice**; active passages used **Verticalities (onset slices)** with **Verticality analysis** = **Time window (summary)** and **Minimum notes per slice** = 3. MusicXML: **written** pitch unless **Apply MusicXML transposition (concert pitch)** was enabled.*

---

## Sidebar

For short explanations of headline metrics, open the multipage guide **Which metric to use?** in the sidebar.
