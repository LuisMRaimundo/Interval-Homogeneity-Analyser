# Canonical MusicXML regression scores

Minimal one-chord MusicXML files used with **`iav/data/canonical_musicxml.json`**. Each file is parsed in **aggregate** mode on **12-EDO** with default dominance homogeneity and **pairwise** headline **H** unless a test overrides settings.

| File | Purpose |
|------|---------|
| `major_triad.xml` | Baseline tertian sonority |
| `minor_triad.xml` | Minor triad contrast |
| `chromatic_cluster.xml` | High adjacent regularity, diverse pairwise cloud |
| `quartal_stack.xml` | Fourth-based stacking |
| `diminished_seventh.xml` | Symmetric seventh |

After editing a score or metrics, run from the repository root:

```bash
python scripts/build_canonical_musicxml.py
pytest tests/test_canonical_musicxml.py
```

See also [docs/MUSICXML_COVERAGE.md](../../docs/MUSICXML_COVERAGE.md) and [TECHNICAL_MANUAL.md](../../TECHNICAL_MANUAL.md) §10.3.
