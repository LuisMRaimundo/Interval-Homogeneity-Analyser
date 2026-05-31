"""Pure UI parameter resolution (no Streamlit imports)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple, cast

from iav.analysis_enums import (
    AnalysisThresholdMode,
    HomogeneityMethod,
    HomogeneityScoreKind,
    IntervallicHeadlineMode,
    MusicXmlImportMode,
    VerticalitySliceMode,
    homogeneity_method_from_str,
    intervallic_headline_mode_from_str,
)
from iav.analysis_presets import (
    HOMOGENEITY_DOMINANCE_LABEL,
    KEY_HEADLINE_METRIC,
    KEY_HOMOGENEITY_SCORING,
    KEY_THRESHOLD_MODE,
)

_FIXED_THRESHOLDS = (0.60, 0.80, 0.30, 0.60)


def homogeneity_method_from_ui_label(label: str) -> HomogeneityMethod:
    """Map Streamlit homogeneity scoring radio text to ``HomogeneityMethod``."""
    if label.startswith("Dominance"):
        return HomogeneityMethod.DOMINANCE
    if label.startswith("Entropy"):
        return HomogeneityMethod.ENTROPY
    return HomogeneityMethod.COMBINED


def score_kind_for_homogeneity_method(method: HomogeneityMethod) -> HomogeneityScoreKind:
    if method == HomogeneityMethod.DOMINANCE:
        return HomogeneityScoreKind.DOMINANCE
    if method == HomogeneityMethod.ENTROPY:
        return HomogeneityScoreKind.CONCENTRATION
    return HomogeneityScoreKind.CONSENSUS


def threshold_tuple_for_mode(mode: AnalysisThresholdMode) -> Tuple[float, float, float, float]:
    if mode == AnalysisThresholdMode.STANDARD:
        raise ValueError("Standard mode thresholds come from sliders, not fixed tuple")
    return _FIXED_THRESHOLDS


def bin_cents_for_edo(edo: int) -> int:
    return int(round(1200 / int(edo)))


def intervallic_headline_from_session(session: Mapping[str, object]) -> IntervallicHeadlineMode:
    raw = session.get(KEY_HEADLINE_METRIC, IntervallicHeadlineMode.PAIRWISE)
    if isinstance(raw, IntervallicHeadlineMode):
        return raw
    return intervallic_headline_mode_from_str(str(raw))


def homogeneity_method_from_session(session: Mapping[str, object]) -> HomogeneityMethod:
    label = str(session.get(KEY_HOMOGENEITY_SCORING, HOMOGENEITY_DOMINANCE_LABEL))
    return homogeneity_method_from_ui_label(label)


@dataclass(frozen=True)
class AnalysisParameterBundle:
    """Resolved analysis knobs for ``metrics_for_notes`` (symbolic aggregate)."""

    remove_duplicates: bool
    edo: int
    bin_cents: int
    dominance_threshold: float
    even_high: float
    even_low: float
    chain_threshold: float
    homogeneity_method: HomogeneityMethod
    score_label: HomogeneityScoreKind
    intervallic_headline_mode: IntervallicHeadlineMode
    alpha_base: float
    auto_alpha: bool
    k_auto: int


def validate_musicxml_slice_combo(
    xml_mode: MusicXmlImportMode | str,
    slice_mode: VerticalitySliceMode | str,
) -> None:
    """Raise ``ValueError`` when slice mode is incompatible with aggregate import."""
    if isinstance(xml_mode, str):
        xml_mode = MusicXmlImportMode(xml_mode)
    if isinstance(slice_mode, str):
        slice_mode = VerticalitySliceMode(slice_mode)
    if xml_mode == MusicXmlImportMode.AGGREGATE and slice_mode != VerticalitySliceMode.SINGLE:
        raise ValueError(
            "Aggregate MusicXML import supports only a single combined sonority; "
            "use onset or sounding verticalities for multi-slice modes."
        )


def analysis_bundle_from_session(
    session: Mapping[str, object],
    *,
    dominance_threshold: float,
    even_high: float,
    even_low: float,
    chain_threshold: float,
) -> AnalysisParameterBundle:
    """Build parameter bundle from session keys plus resolved thresholds."""
    edo = int(cast(Any, session.get("iav_edo", 12)))
    method = homogeneity_method_from_session(session)
    return AnalysisParameterBundle(
        remove_duplicates=bool(session.get("iav_remove_duplicates", True)),
        edo=edo,
        bin_cents=bin_cents_for_edo(edo),
        dominance_threshold=dominance_threshold,
        even_high=even_high,
        even_low=even_low,
        chain_threshold=chain_threshold,
        homogeneity_method=method,
        score_label=score_kind_for_homogeneity_method(method),
        intervallic_headline_mode=intervallic_headline_from_session(session),
        alpha_base=float(cast(Any, session.get("iav_alpha_base", 0.55))),
        auto_alpha=bool(session.get("iav_auto_alpha", False)),
        k_auto=int(cast(Any, session.get("iav_k_auto", 4))),
    )


def homogeneity_method_value_for_metrics(method: HomogeneityMethod) -> str:
    return homogeneity_method_from_str(method).value
