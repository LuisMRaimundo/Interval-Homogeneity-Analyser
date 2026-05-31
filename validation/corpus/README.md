# MusicXML corpus (regression)

Small **synthetic** scores that stress the parser beyond the minimal `validation/fixtures/`
cases. They are **not** a substitute for a large export corpus from Sibelius, Dorico,
Finale, MuseScore, etc., but they catch regressions on:

- multiple `<voice>` entries in one measure
- `<backup>` / `<forward>` cursor motion
- explicit `<alter>` with `<accidental>` (double-flat style)

Add new `.xml` files here and extend `tests/test_corpus_musicxml.py` if you need
assertions beyond “parses without error”.
