"""Estimate distance to the target from its apparent size on screen.

In a third-person view a creature that is far away covers fewer pixels than the
same creature up close, so comparing the target's on-screen footprint against a
reference measurement gives a usable near/far signal without any memory access.
"""

from __future__ import annotations

from typing import Optional


def estimate_distance(
    measured_pixels: int,
    reference_pixels: int,
    near_ratio: float = 0.55,
    far_ratio: float = 0.20,
) -> Optional[str]:
    """Classify target distance as ``near``, ``far`` or ``unknown``.

    ``reference_pixels`` is the apparent size of the target measured when it is
    known to be at attack range. Thresholds are relative, so they work for any
    creature size once a reference is captured.
    """
    if measured_pixels <= 0 or reference_pixels <= 0:
        return None
    ratio = measured_pixels / reference_pixels
    if ratio >= near_ratio:
        return "near"
    if ratio <= far_ratio:
        return "far"
    return None
