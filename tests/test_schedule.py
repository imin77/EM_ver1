from datetime import date

from models import Plan, Point, Schedule
from services.schedule import generate
from models import db


def test_generate_weekly_creates_entries(app):
    with app.app_context():
        plan = Plan.query.first()
        start = date(2024, 1, 1)
        created = generate(plan, start, 2)
        assert len(created) == 2 * Point.query.count()
        # Re-running should not duplicate
        created_again = generate(plan, start, 2)
        assert len(created_again) == 0
        assert Schedule.query.count() == len(created)


def test_generate_monthly_interval(app):
    with app.app_context():
        plan = Plan(site_id=1, name="Monthly", frequency="monthly")
        db.session.add(plan)
        db.session.commit()
        start = date(2024, 1, 1)
        created = generate(plan, start, 2)
        dates = sorted({s.date for s in created})
        assert dates == [start, date(2024, 1, 29)]
