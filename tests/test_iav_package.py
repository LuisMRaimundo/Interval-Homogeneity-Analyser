"""Smoke tests for the iav package layout."""

from iav import FORCE_DEDUPE_THRESHOLD, MAX_NOTES
from iav.constants import FORCE_DEDUPE_THRESHOLD as FD2
from iav.constants import MAX_NOTES as M2


def test_constants_exported():
    assert MAX_NOTES == M2 == 500
    assert FORCE_DEDUPE_THRESHOLD == FD2 == 200
