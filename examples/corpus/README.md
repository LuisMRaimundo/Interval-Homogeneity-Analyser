# Example corpus (canonical sonorities)

Each `.json` file lists `notes` as `[letter, alter, octave]` rows (same tuple shape as manual parsing after `parse_manual_note_string`). Optional fields in manifest entries are documented in `iav/data/canonical_sonorities.json`.

Batch analysis:

```bash
python analyze_corpus.py --input examples/corpus --output results/
# Concert-pitch MusicXML (when files use <transpose>):
python analyze_corpus.py -i examples/corpus -o results/ --sounding-transpose
```

Verify frozen regression expectations (no Streamlit):

```bash
python analyze_corpus.py --verify-canonical -i examples/corpus -o results/
```

Regenerate expectations after intentional metric changes:

```bash
python scripts/generate_canonical_expectations.py
```
