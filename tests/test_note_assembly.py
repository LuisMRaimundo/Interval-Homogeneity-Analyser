"""Tests for manual vs MusicXML note assembly (no Streamlit)."""

from iav.note_sources import assemble_notes_from_manual_and_xml


def test_xml_only_when_merge_false_excludes_manual_notes():
    manual = [("C", 0.0, 4), ("D", 0.0, 4)]
    xml = [("E", 0.0, 4)]
    out = assemble_notes_from_manual_and_xml(manual, xml, has_xml_upload=True, merge_manual=False)
    assert out == xml


def test_no_xml_always_uses_manual_notes():
    manual = [("E", 0.0, 4)]
    xml = [("G", 0.0, 4)]
    assert (
        assemble_notes_from_manual_and_xml(manual, xml, has_xml_upload=False, merge_manual=False)
        == manual
    )
    assert (
        assemble_notes_from_manual_and_xml(manual, xml, has_xml_upload=False, merge_manual=True)
        == manual
    )


def test_xml_merge_true_combines_manual_and_xml():
    manual = [("F", 1.0, 3)]
    xml = [("A", 0.0, 4)]
    out = assemble_notes_from_manual_and_xml(manual, xml, has_xml_upload=True, merge_manual=True)
    assert out == manual + xml


def test_xml_merge_true_but_empty_manual_yields_xml_only():
    manual = []
    xml = [("B", 0.0, 3)]
    out = assemble_notes_from_manual_and_xml(manual, xml, has_xml_upload=True, merge_manual=True)
    assert out == xml
