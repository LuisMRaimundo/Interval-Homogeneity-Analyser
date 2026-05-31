"""Regression tests for MusicXML parsing (mirrors validation/fixtures)."""

import pathlib

from analysis_core import (
    parse_musicxml_bytes,
    parse_musicxml_bytes_with_sounding_transpose,
    parse_musicxml_sounding_verticalities_bytes,
    parse_musicxml_verticalities_bytes,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "validation" / "fixtures"


def read_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_tie_direct():
    slices, _ = parse_musicxml_sounding_verticalities_bytes(read_fixture("tie_direct.xml"))
    assert len(slices) == 1
    assert (slices[0]["start"], slices[0]["end"]) == (0.0, 2.0)
    assert len(slices[0]["notes"]) == 1


def test_tie_notations():
    slices, _ = parse_musicxml_sounding_verticalities_bytes(read_fixture("tie_notations.xml"))
    assert len(slices) == 1
    assert (slices[0]["start"], slices[0]["end"]) == (0.0, 2.0)


def test_transpose_applied_with_sounding_transpose_api():
    notes, _ = parse_musicxml_bytes_with_sounding_transpose(read_fixture("transpose.xml"))
    assert len(notes) == 1
    letter, alter, octave = notes[0]
    assert letter == "D"
    assert alter == 0.0
    assert octave == 4


def test_transpose_ignored_by_default_matches_written_pitch():
    notes, _ = parse_musicxml_bytes(read_fixture("transpose.xml"))
    assert len(notes) == 1
    assert notes[0][0] == "C" and notes[0][1] == 0.0 and notes[0][2] == 4


_OCTAVE_CHANGE_FIXTURE = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <transpose><chromatic>0</chromatic><octave-change>1</octave-change></transpose>
      </attributes>
      <note>
        <pitch><step>B</step><octave>4</octave></pitch>
        <duration>1</duration>
      </note>
    </measure>
  </part>
</score-partwise>
"""


def test_transpose_octave_change_respells():
    notes, _ = parse_musicxml_bytes_with_sounding_transpose(_OCTAVE_CHANGE_FIXTURE)
    assert len(notes) == 1
    letter, alter, octave = notes[0]
    assert letter == "B"
    assert abs(float(alter)) < 1e-9
    assert octave == 5


def test_grace_in_onset():
    slices, _ = parse_musicxml_verticalities_bytes(
        read_fixture("grace.xml"), include_grace=True, include_cue=False
    )
    # Grace consumes no duration; grace D and attacked E share the same onset.
    assert len(slices) == 1
    assert len(slices[0]["notes"]) == 2


# Sibelius-style: <alter>0</alter> + microtonal <accidental> (true offset only in accidental).
_SIBELIUS_QS = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.0">
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note>
        <pitch><step>C</step><alter>0</alter><octave>5</octave></pitch>
        <duration>1</duration>
        <accidental>quarter-sharp</accidental>
      </note>
    </measure>
  </part>
</score-partwise>
"""

_SIBELIUS_QF = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.0">
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note>
        <pitch><step>D</step><alter>0</alter><octave>7</octave></pitch>
        <duration>1</duration>
        <accidental>quarter-flat</accidental>
      </note>
    </measure>
  </part>
</score-partwise>
"""


def test_sibelius_style_microtone_uses_accidental_when_alter_zero():
    notes, skipped = parse_musicxml_bytes(_SIBELIUS_QS)
    assert skipped == 0
    assert len(notes) == 1
    assert notes[0] == ("C", 0.5, 5)

    notes2, skipped2 = parse_musicxml_bytes(_SIBELIUS_QF)
    assert skipped2 == 0
    assert notes2[0] == ("D", -0.5, 7)


def test_fractional_alter_without_accidental_unchanged():
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.0">
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions></attributes>
      <note>
        <pitch><step>E</step><alter>0.5</alter><octave>4</octave></pitch>
        <duration>1</duration>
      </note>
    </measure>
  </part>
</score-partwise>
"""
    notes, skipped = parse_musicxml_bytes(xml)
    assert skipped == 0
    assert notes[0] == ("E", 0.5, 4)


_IGNORE_TRANSPOSE_FIXTURE = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1"><part-name>Part</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <transpose><chromatic>-2</chromatic></transpose>
      </attributes>
      <note>
        <pitch><step>D</step><octave>4</octave></pitch>
        <duration>1</duration>
      </note>
    </measure>
  </part>
</score-partwise>
"""


def test_written_pitch_vs_sounding_transpose_paths():
    notes_sounding, _ = parse_musicxml_bytes_with_sounding_transpose(_IGNORE_TRANSPOSE_FIXTURE)
    assert len(notes_sounding) == 1
    letter, alter, octave = notes_sounding[0]
    assert letter == "C"
    assert abs(float(alter)) < 1e-9
    assert octave == 4

    notes_written, _ = parse_musicxml_bytes(_IGNORE_TRANSPOSE_FIXTURE)
    assert notes_written[0] == ("D", 0.0, 4)
