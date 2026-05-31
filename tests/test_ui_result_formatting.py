"""Result formatting helpers."""

from iav.ui_result_formatting import classification_display, interval_heterogeneity


def test_classification_display_empty():
    assert classification_display("") == "(no classification)"


def test_interval_heterogeneity_none():
    assert interval_heterogeneity(None) is None
