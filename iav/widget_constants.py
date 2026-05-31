"""Static UI option lists for the manual-note panel."""

from __future__ import annotations

from typing import List, Tuple

# (menu label, accidental suffix after A–G — parser accepts these strings)
ACCIDENTAL_CHOICES: List[Tuple[str, str]] = [
    ("Natural (nothing after the letter)", ""),
    ("Half step sharp — type # (e.g. C#)", "#"),
    ("Half step flat — type b (e.g. Cb)", "b"),
    ("Double sharp — ##", "##"),
    ("Double flat — bb", "bb"),
    ("Quarter-tone sharp (+½ semitone) — +", "+"),
    ("Quarter-tone flat (−½ semitone) — -", "-"),
    ("Three-quarter-tone sharp — 1.5", "1.5"),
    ("Three-quarter-tone flat — -1.5", "-1.5"),
]
