"""Result judgement helper."""

from __future__ import annotations

from typing import Optional

from models import Method


def judge(value: Optional[float], qual: Optional[str], method: Method) -> str:
    """Return judgement string for a result.

    Args:
        value: Numeric measurement value.
        qual: Qualitative measurement text (e.g. "Absent").
        method: Method instance containing limit definition.

    Returns:
        "Pass", "Fail", or "Review" if decision cannot be made.
    """

    if method.limit_type == "PresenceAbsence":
        if qual is None:
            return "Review"
        return "Pass" if qual.strip().lower() == "absent" else "Fail"

    if value is None:
        return "Review"

    if method.limit_type == "Max":
        if method.max_val is None:
            return "Review"
        return "Pass" if value <= method.max_val else "Fail"

    if method.limit_type == "Min":
        if method.min_val is None:
            return "Review"
        return "Pass" if value >= method.min_val else "Fail"

    if method.limit_type == "Range":
        if method.min_val is None or method.max_val is None:
            return "Review"
        return "Pass" if method.min_val <= value <= method.max_val else "Fail"

    return "Review"
