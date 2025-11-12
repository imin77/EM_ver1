"""Simple seed script for development."""

from app import create_app, db
from models import Method, Point, Site, Zone


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        if not Site.query.filter_by(name="Seoul Plant").first():
            site = Site(name="Seoul Plant")
            db.session.add(site)
            db.session.flush()
            zone = Zone(site_id=site.id, name="Packaging", risk_level="High")
            db.session.add(zone)
            point = Point(zone_id=zone.id, code="PKG-01", name="Conveyor Belt", type="Surface")
            db.session.add(point)
        if not Method.query.filter_by(code="TBC").first():
            method = Method(
                code="TBC",
                name="Total Bacterial Count",
                unit="CFU/25cm2",
                limit_type="Max",
                max_val=10,
            )
            db.session.add(method)
        db.session.commit()
        print("Seed data created")


if __name__ == "__main__":
    seed()
