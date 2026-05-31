"""Static copy for the 'which metric to use?' guide (Streamlit + docs)."""

METRIC_GUIDE_SECTIONS = [
    {
        "title": "Headline H is not one single thing",
        "body": (
            "The slider labelled **H** always reflects the **headline intervallic metric** you selected "
            "under *Homogeneity model settings*. The four constructions below are **always computed** "
            "in *Intervallic metric suite*; only the headline choice changes **H**, **H label**, and slice **ΔH**."
        ),
    },
    {
        "title": "pairwise_intervallic_concentration (default)",
        "when": (
            "Use when you want the **global distribution** of all unordered pitch-distance pairs "
            "(how concentrated the full interval multiset is)."
        ),
        "example": "Comparing two dense verticalities by overall interval content, regardless of voice order.",
        "caveat": "Chromatic clusters score low here even when every adjacent step is a semitone.",
    },
    {
        "title": "intervallic_adjacency_regularity",
        "when": (
            "Use for **generative** or **locally regular** textures: chromatic clusters, whole-tone chains, "
            "quartal stacks, microtonal strata built from repeating adjacent steps."
        ),
        "example": "C–D♭–D–E♭–E–F → adjacent steps all m2 → high adjacent score; pairwise cloud stays diverse.",
        "caveat": "Ignores long-range intervals; two aggregates with the same adjacent pattern but different spans differ in pairwise scores.",
    },
    {
        "title": "proximity_weighted_linear",
        "when": (
            "Use when you need **all pairs** but want **nearby register neighbours** to matter more, "
            "with weights **1/|i−j|** after sorting by pitch height."
        ),
        "example": "Masses where local interval repetition matters but distant pairs should still contribute weakly.",
        "caveat": "Weights are ordinal (sorted index gap), not voice-leading paths from the score.",
    },
    {
        "title": "proximity_weighted_quadratic",
        "when": (
            "Same intent as the linear variant, but weights **1/|i−j|²** — even stronger emphasis on "
            "immediately adjacent pitches."
        ),
        "example": "Dense clusters where only nearest neighbours should drive the headline score.",
        "caveat": "Very distant pairs contribute little; compare with the linear variant in the metric suite.",
    },
    {
        "title": "hybrid_intervallic_homogeneity",
        "when": (
            "Use only as a **synthetic summary**, with **α declared**. "
            "H = α·adjacent + (1−α)·pairwise (same dominance or entropy path as above)."
        ),
        "example": "α = 0.6 emphasises local/generative regularity; α = 0.5 balances; α = 0.3 keeps global pairwise emphasis.",
        "caveat": "Not a standard textbook index—report α whenever you cite hybrid H.",
    },
    {
        "title": "What this tool does not measure",
        "body": (
            "**Registral dispersion**, **auditory consonance**, **timbral fusion**, and **perceptual homogeneity** "
            "are out of scope. Interval labels are **pitch-distance bins** on the chosen EDO grid, not spelling-aware voice leading."
        ),
    },
]
