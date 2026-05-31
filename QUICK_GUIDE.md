# Interface quick guide

Short guide for **non-specialists**: what each option does and **when to use it**. The tool measures **pitch distances** (symbolic intervals on the grid you choose), not “how the orchestra sounds”.

**Fixed workflow (thesis / many examples):** [ANALYSIS_PRESET.md](ANALYSIS_PRESET.md) — presets ①–④, pairwise headline **H** by default, exact UI labels.

---

## 0. Analysis presets (start here for comparable runs)

At the top of the main page, open **Analysis presets**:

1. Choose **What are you analysing?** (① manual chord → one **H**; ②③ one chord from XML; ④ passage → many **H** + timeline charts).
2. Click **Apply preset now**, or leave **Automatically apply selected preset** on.

Presets set **Fixed thresholds**, **Dominance (max share)**, and **Global pairwise concentration (default)** as headline **H**. Details: [ANALYSIS_PRESET.md](ANALYSIS_PRESET.md).

---

## 1. Manual input

- **Note table** (one column)
  - Type notes the usual way: **C4**, **F#3**, **Bb5**, **C+4** (quarter-sharp in octave 4).
  - If you omit the number (**C**, **Eb**), the app assumes octave **4**.

- **Accidental reference** (submenu)
  Reminder for sharps, flats, and microtones. For **quarter tones**, pick **24-EDO** or **48-EDO** below; otherwise rounding can erase the detail.

**When to use:** chords or sonorities you already know by heart, with no MusicXML file.

---

## 2. MusicXML upload

- **Upload file**
  Accepts `.xml`, `.musicxml`, or `.mxl` (zip).

- **Import mode**
  - **Aggregate (all notes)** — Puts **all** pitches from the file in one pool. Simple, but long scores become huge lists. Best for **short excerpts** or files already trimmed to the sonority you care about.
  - **Verticalities (onset slices)** — Slices by **attack time**: “what sounds together at the same metric time”. Good for **chords across the piece**.
  - **Sounding verticalities** — Tracks **notes that stay sounding** between two times (ties and durations). Good for **sustained harmony** over time. Only notes with **duration > 0** count; grace notes usually **do not** enter (no duration in this model).

- **Apply MusicXML transposition (concert pitch)**
  **Off (default)** — reads **written** `<pitch>`; `<transpose>` tags are ignored (prepare the score accordingly).
  **On** — applies each measure’s `<transpose>` for **sounding** concert pitch (Bb clarinet, horn in F, etc.). Batch CLI: **`--sounding-transpose`**.

- **Minimum notes per slice**
  Only for slice modes: drops slices with **too few notes** (e.g. a single melodic line). Raise it if you want **only fuller chords**.

- **Include grace notes** (onset slices only)
  Includes **grace notes** at the same time as the “main” note. Turn on if ornaments matter musically; turn off to focus on the harmonic skeleton.

- **Include cue notes** (onset slices only)
  Includes **cue notes** (often editorial suggestions). Usually **off**.

- **Verticality analysis** (how slices are used)
  - **Single slice** — Pick **one** slice from a list (good for exploration).
  - **All slices (summary)** — **Line chart of H over score time**, **vertical note-count chart**, summary table, **`slice_summary.csv`**, and **`vertical_cardinality_profile.json`**. Use for a whole excerpt or busy page.
  - **Time window (summary)** — Same charts, table, and downloads, but only slices **inside a time range** (quarter-note slider). Best for **one active passage** (e.g. a single score page).

- **Warning (Aggregate + many notes)**
  If you see *“treats ALL pitched notes as one aggregate (no time slicing)”*, switch to **Verticalities** (or Sounding). **Collapse duplicates** does not fix time — it only merges repeated pitches at the same height.

- **Include manual notes in analysis**
  Only appears if you uploaded XML **and** have valid rows in the manual table. **On** = merge both sources; **off** = file only.

**Quick choice**

| Situation | Import mode |
|-----------|-------------|
| One chord or ~10 notes in a small file | **Aggregate** |
| Successive chords / active orchestral page | **Verticalities** + **Time window** |
| Sustained chords, ties matter | **Sounding verticalities** + **Time window** |

---

## 3. Data preparation

- **Collapse to unique pitches**
  **On (recommended)** — Repeated pitches at the same height count **once** (useful for orchestrated chords with doublings).
  **Off** — Keeps duplicates; interval counts **multiply**.

**When to turn off:** rarely; only if you want to count **each written note** separately.

---

## 4. Tuning system (EDO)

- **12 / 24 / 48** — **Larger** numbers mean a **finer** pitch grid (more steps per octave).
  - **12** — Same as “normal” piano; interval names like major third, perfect fourth.
  - **24 or 48** — For **quarter tones** or finer divisions; avoids microtones vanishing in rounding.

**Quick choice:** semitone music → **12**; quarter tones in the score → **24** or **48**.

---

## 5. “Standard” vs “Fixed thresholds”

- **Standard**
  Lets you **tune** thresholds in “Labeling settings” (interval dominance, evenness, chain regularity). For **experimenting** or fitting the problem.

- **Fixed thresholds (heuristic)**
  Uses **fixed** preset values (0.60 / 0.80 / 0.30, etc.) and shows explanatory text. For **always the same yardstick** without touching sliders.

**Quick choice:** explore → **Standard**; simplicity and fixed comparability → **Fixed**.

---

## 6. Homogeneity (“Homogeneity model settings”)

This is an **app heuristic**, not a single academic definition.

- **Dominance (max share)**
  Asks: “**Is one interval type winning** the histogram?” (largest share). Simple and easy to read.

- **Entropy concentration**
  Looks at the **whole** interval distribution, not only the winner. Often **more stable** when many interval types appear. The app normalises entropy using the **pitch span** of the sonority (so similar registral “room” is compared on the same footing), not only how many different interval sizes showed up. Details: [TECHNICAL_MANUAL.md §4.4](TECHNICAL_MANUAL.md).

- **Combined view**
  Shows **both** views plus a **consensus** (geometric mean). Good for **seeing agreement or tension** between criteria.

- **Headline intervallic metric** (what becomes **H**)
  - **Pairwise intervallic concentration** (default) — All unordered distances on the grid; best default for “chord as interval cloud”.
  - **Intervallic adjacency regularity** — Steps between **sorted** neighbours only (scale-like stacks).
  - **Proximity-weighted (linear / quadratic)** — Pairwise distances weighted by register separation ($1/|j-i|$ or $1/|j-i|^2$).
  - **Hybrid intervallic homogeneity** — Blend of adjacent + pairwise with **α** (see below).

- **Intervallic metric suite** (expander)
  Always lists all four constructions even when only one is the headline—useful to compare chain vs cloud without re-running.

- **Alpha / Auto-adjust / k**
  Matter **only** when headline mode is **Hybrid**. Otherwise you can ignore them.

**Sidebar:** open **Which metric to use?** for a short decision guide (pairwise vs adjacent vs weighted vs hybrid).

**Quick choice**

| Goal | Option |
|------|--------|
| Compare different chords with the same logic | **Entropy** or **Dominance**, headline **pairwise** |
| “Is there one dominant interval?” | **Dominance** |
| Richer report | **Combined** |
| Voicing / scale fragment in register | Headline **adjacent** or **hybrid** with higher α |
| Emphasise nearby pitch pairs | **Proximity-weighted** |

---

## 7. After loading

- The app needs **at least two notes** to compute intervals.
- In **Aggregate**, more than **50 notes** triggers a **warning**: all pitches are one sonority (use **Verticalities** for passages).
- You can **edit** extracted notes in the tables shown before analysis (useful to fix odd reads).

---

## 8. Batch analysis (optional, no UI)

For many sonorities or thesis tables, from the project folder:

```bash
pip install -e .
python analyze_corpus.py --input examples/corpus --output results/
python analyze_corpus.py -i examples/corpus -o results/ --headline pairwise_intervallic_concentration --sounding-transpose
```

See [README.md](README.md) and [TECHNICAL_MANUAL.md §10](TECHNICAL_MANUAL.md).

---

## 9. One-minute recap

1. **Apply an analysis preset** (①–④) or match [ANALYSIS_PRESET.md](ANALYSIS_PRESET.md) settings by hand.
2. **Pick the source:** manual only, XML only, or both (merge).
3. **Pick import mode** from the score: isolated chord → Aggregate; harmonic timeline → Verticalities or Sounding.
4. **EDO 12** unless you have microtones → 24/48.
5. **Keep “Collapse duplicates” on** for typical chords (turn off only if doublings must count).
6. **Homogeneity:** presets use **Dominance** + headline **pairwise**; open **Which metric to use?** if you switch to adjacent, hybrid, or entropy.

After analysis, optional **Intervallic context** shows mod-12 interval-vector evenness and reference **interval** fingerprints.

For MusicXML **All slices** or **Time window** modes, the app shows a **line chart of H across score time**, a **vertical note-count chart** (how many notes per chord moment — symbolic thickness, not loudness or acoustic density), a table with **ΔH** (change vs the previous slice), **`slice_summary.csv`**, and **`vertical_cardinality_profile.json`**. The second chart plots **note count only**; tooltips may show **Unique pitches** and **PC cardinality** when those columns exist. In JSON, **pitch-class cardinality** is omitted (`null`) unless the table has an explicit **PC cardinality** column (e.g. C4+C5 is two notes but one pitch class — the app does not guess). Registral dispersion is **not** handled here.

For **manual** or **aggregate** analysis (one sonority), download **`vertical_cardinality_profile.json`** in the **Export** section (one slice at time 0, with all three metrics when 12-EDO applies).

For math detail and technical limits, see [TECHNICAL_MANUAL.md](TECHNICAL_MANUAL.md) (§1.3, §10, §12).
