"""Homogeneity metrics edge cases."""

from interval_analysis import h_band_label, homogeneity_score, metrics_for_notes


def test_two_notes_perfect_homogeneity_dominance():
    notes = [("C", 0.0, 4), ("G", 0.0, 4)]
    h, chain, pair, ic, dc, adj, *_ = homogeneity_score(
        notes, alpha=0.5, method="dominance", bin_cents=100
    )
    assert dc == {7: 1}
    assert pair == 1.0
    assert chain == 1.0
    assert h == 1.0


def test_metrics_combined_two_notes():
    notes = [("D", 0.0, 4), ("F", 0.0, 4)]
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "combined", bin_cents=100)
    assert m["H_consensus"] is not None
    assert m["total_intervals"] == 1


def test_dyad_entropy_homogeneity_is_maximal():
    """Single pairwise interval class → concentrated distribution → H = 1.0 under entropy mode."""
    notes = [("C", 0.0, 4), ("E", 0.0, 4)]
    h, chain, pair, _, _, _, *_ = homogeneity_score(
        notes, alpha=0.5, method="entropy", bin_cents=100
    )
    assert pair == 1.0
    assert chain == 1.0
    assert h == 1.0
    m = metrics_for_notes(notes, 0.35, 0.8, 0.3, 0.7, "entropy", bin_cents=100)
    assert m["H"] == 1.0
    assert m["H_label"] == h_band_label(1.0) == "homogeneous"
    assert "pairwise" in m["H_primary_title"].lower()
    assert "entropy" in m["H_primary_help"].lower()
    assert "H_primary_help" in m and "entropy" in m["H_primary_help"].lower()


def test_chromatic_stack_entropy_chain_max_pair_diverse():
    """Consecutive semitone cluster: adjacent steps are all identical → chain concentration 1.0."""
    notes = [
        ("C", 0.0, 4),
        ("C", 1.0, 4),
        ("D", 0.0, 4),
        ("D", 1.0, 4),
        ("E", 0.0, 4),
    ]
    m = metrics_for_notes(
        notes, 0.35, 0.8, 0.3, 0.7, "entropy", bin_cents=100, chain_threshold=0.60
    )
    assert m["chain_score"] == 1.0
    assert m["pair_score"] < 1.0
    assert "uniform stacking" in m["classification"]
