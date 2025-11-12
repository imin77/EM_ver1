"""Schedule generation service."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List

from models import Plan, Point, Schedule, db


def _get_points_for_plan(plan: Plan) -> Iterable[Point]:
    """Return points associated with the plan's site."""
    return Point.query.join(Point.zone).filter_by(site_id=plan.site_id).all()


def generate(plan: Plan, start_date: date, periods: int) -> List[Schedule]:
    """Generate schedules for the given plan.

    Args:
        plan: Plan to schedule.
        start_date: Start date for the first period.
        periods: Number of periods (weeks or months) to generate.

    Returns:
        List of Schedule objects that were created and committed.
    """

    created: List[Schedule] = []
    points = list(_get_points_for_plan(plan))
    if not points:
        return created

    delta = timedelta(weeks=1)
    if plan.frequency == "monthly":
        delta = timedelta(weeks=4)

    for i in range(periods):
        scheduled_date = start_date + delta * i
        for point in points:
            exists = Schedule.query.filter_by(
                plan_id=plan.id, point_id=point.id, date=scheduled_date
            ).first()
            if exists:
                continue
            schedule = Schedule(plan_id=plan.id, date=scheduled_date, point_id=point.id)
            db.session.add(schedule)
            created.append(schedule)

    db.session.commit()
    return created
