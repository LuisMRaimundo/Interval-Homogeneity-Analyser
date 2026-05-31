"""Enumerated analysis / UI modes (canonical values, not ad-hoc string literals)."""

from __future__ import annotations

from enum import Enum


class HomogeneityMethod(str, Enum):
    """How pairwise homogeneity H is derived for the headline score."""

    DOMINANCE = "dominance"
    ENTROPY = "entropy"
    COMBINED = "combined"


class IntervallicHeadlineMode(str, Enum):
    """
    Which intervallic concentration score is shown as headline H.

    Pairwise and adjacent are always computed for diagnostics; weighted variants
    use pitch-sorted indices and weights 1/|j-i|^p on unordered pairs.
    """

    PAIRWISE = "pairwise_intervallic_concentration"
    ADJACENT = "intervallic_adjacency_regularity"
    WEIGHTED_LINEAR = "proximity_weighted_linear"
    WEIGHTED_QUADRATIC = "proximity_weighted_quadratic"
    HYBRID = "hybrid_intervallic_homogeneity"


def intervallic_headline_mode_from_str(
    value: str | IntervallicHeadlineMode,
) -> IntervallicHeadlineMode:
    if isinstance(value, IntervallicHeadlineMode):
        return value
    return IntervallicHeadlineMode(value)


class HomogeneityScoreKind(str, Enum):
    """Short label for secondary score columns (mirrors prior ``score_label`` strings)."""

    DOMINANCE = "dominance"
    CONCENTRATION = "concentration"
    CONSENSUS = "consensus"


class MusicXmlImportMode(str, Enum):
    """MusicXML ingestion strategy (values match Streamlit radio labels)."""

    AGGREGATE = "Aggregate (all notes)"
    ONSET_VERTICALITIES = "Verticalities (onset slices)"
    SOUNDING_VERTICALITIES = "Sounding verticalities"


class VerticalitySliceMode(str, Enum):
    """How verticality slices are summarized or chosen."""

    SINGLE = "Single slice"
    ALL_SLICES = "All slices (summary)"
    TIME_WINDOW = "Time window (summary)"


class AnalysisThresholdMode(str, Enum):
    """Whether aggregate thresholds are user-tunable or fixed for explanation mode."""

    STANDARD = "Standard"
    FIXED_HEURISTIC = "Fixed thresholds (heuristic)"


def homogeneity_method_from_str(value: str | HomogeneityMethod) -> HomogeneityMethod:
    if isinstance(value, HomogeneityMethod):
        return value
    return HomogeneityMethod(value)
