"""
Interval aggregates, homogeneity metrics, and 12-TET pitch-class / set-class helpers.

Canonical sounding height is ``iav.pitch_model.chromatic_midi_float`` (re-exported as ``chromatic_midi_float`` here).
``NoteTuple`` spellings are for I/O and display; interval sizes and homogeneity use quantized MIDI/cents.

Pairwise labels are pitch-distance summaries on the selected EDO grid (not spelling-aware).
Set-class tools (prime form, interval vector) follow the usual Forte / pitch-class set tradition
and apply only when the tuning is 12-EDO and each pitch maps to an integer chromatic step.
"""

from __future__ import annotations

from iav.aggregate_metrics import AggregateHomogeneityMetrics
from iav.analysis_enums import (
    HomogeneityMethod,
    IntervallicHeadlineMode,
    homogeneity_method_from_str,
    intervallic_headline_mode_from_str,
)
from iav.note_types import NoteTuple
from iav.pitch_model import chromatic_midi_float
from iav.set_class_12tet import (
    format_prime_form,
    interval_vector_12tet,
    interval_vector_string,
    normal_order_12tet,
    pitch_class_int_from_note,
    pitch_classes_12tet_unique,
    prime_form_12tet,
    set_class_summary_12tet,
)

from ._edo_labels import (
    ACC_TO_SEMITONES,
    ENHARMONIC_SIMPLE,
    format_note_display_label,
    format_note_spelling,
    interval_name,
    intervals_for_notes,
    note_to_units,
    parse_manual_note_string,
    parse_note_name,
    quantize_units,
    semitone_to_label,
    units_to_label,
)
from ._homogeneity import (
    adjacent_interval_counts_from_notes,
    classify_aggregate,
    cluster_compactness,
    dominance,
    dominant_item,
    entropy_evenness,
    entropy_evenness_supportbounded,
    h_band_label,
    homogeneity_score,
    intervallic_concentration,
    pairwise_distance_support_bins,
    pairwise_pitch_span_units,
    proximity_weighted_distance_counts,
    resolve_headline_h,
    sorted_pitch_units,
    type_concentration,
)
from ._manual_input import (
    compute_alpha_used,
    dedupe_notes_by_midi,
    looks_like_octave_shorthand_in_note_field,
    manual_input_hints,
    normalize_manual_notes,
)
from ._metrics_for_notes import metrics_for_notes

__all__ = [
    "ACC_TO_SEMITONES",
    "ENHARMONIC_SIMPLE",
    "AggregateHomogeneityMetrics",
    "HomogeneityMethod",
    "IntervallicHeadlineMode",
    "NoteTuple",
    "homogeneity_method_from_str",
    "intervallic_headline_mode_from_str",
    "adjacent_interval_counts_from_notes",
    "chromatic_midi_float",
    "classify_aggregate",
    "cluster_compactness",
    "compute_alpha_used",
    "dedupe_notes_by_midi",
    "dominance",
    "dominant_item",
    "entropy_evenness",
    "entropy_evenness_supportbounded",
    "format_note_display_label",
    "format_note_spelling",
    "h_band_label",
    "homogeneity_score",
    "intervallic_concentration",
    "interval_name",
    "proximity_weighted_distance_counts",
    "resolve_headline_h",
    "sorted_pitch_units",
    "intervals_for_notes",
    "manual_input_hints",
    "metrics_for_notes",
    "normalize_manual_notes",
    "note_to_units",
    "pairwise_distance_support_bins",
    "pairwise_pitch_span_units",
    "parse_manual_note_string",
    "parse_note_name",
    "quantize_units",
    "semitone_to_label",
    "type_concentration",
    "units_to_label",
    "looks_like_octave_shorthand_in_note_field",
    "format_prime_form",
    "interval_vector_12tet",
    "interval_vector_string",
    "normal_order_12tet",
    "pitch_class_int_from_note",
    "pitch_classes_12tet_unique",
    "prime_form_12tet",
    "set_class_summary_12tet",
]
