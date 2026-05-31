"""Aggregate classification: chain stacking suffix and H-band labels."""

from interval_analysis import h_band_label, metrics_for_notes


def test_h_band_label_boundaries():
    assert h_band_label(0.80) == "homogeneous"
    assert h_band_label(0.79) == "moderately homogeneous"
    assert h_band_label(0.50) == "moderately homogeneous"
    assert h_band_label(0.49) == "moderately heterogeneous"
    assert h_band_label(0.20) == "moderately heterogeneous"
    assert h_band_label(0.19) == "heterogeneous"


def test_chromatic_cluster_regular_stacking():
    """Five consecutive semitones: identical adjacent intervals → high chain dominance."""
    notes = [
        ("C", 0.0, 4),
        ("C", 1.0, 4),
        ("D", 0.0, 4),
        ("D", 1.0, 4),
        ("E", 0.0, 4),
    ]
    m = metrics_for_notes(
        notes, 0.35, 0.8, 0.3, 0.7, "dominance", bin_cents=100, chain_threshold=0.60
    )
    assert m["chain_score"] == 1.0
    assert "uniform stacking" in m["classification"]
    assert "H_label" in m


def test_dispersed_sonority_irregular_stacking():
    """Wide, uneven gaps between sorted pitches → low adjacent-interval dominance."""
    notes = [
        ("C", 0.0, 2),
        ("G", 0.0, 5),
        ("E", 0.0, 6),
        ("B", 0.0, 3),
    ]
    m = metrics_for_notes(
        notes, 0.35, 0.8, 0.3, 0.7, "dominance", bin_cents=100, chain_threshold=0.60
    )
    assert m["chain_score"] < 0.60
    assert "irregular stacking" in m["classification"]


def test_metrics_includes_h_label_combined():
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "combined", bin_cents=100)
    assert m["H_label"] == h_band_label(m["H_consensus"])
