"""
Backward-compatible shim: interval / homogeneity analytics live in ``iav.interval_analysis_core``.

12-TET set-class helpers are implemented in ``iav.set_class_12tet`` and re-exported here.

Prefer ``from iav.interval_analysis_core import ...`` (or ``iav.note_types.NoteTuple``) in new code.
"""

from __future__ import annotations

import iav.interval_analysis_core as _iac
from iav.interval_analysis_core import *  # noqa: F403

__all__ = list(_iac.__all__)
