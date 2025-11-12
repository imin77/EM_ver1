import pytest
from flask import Flask

from app import create_app, db
from models import Method, Plan, Point, Site, Zone


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        site = Site(name="Test Site")
        db.session.add(site)
        db.session.flush()
        zone = Zone(site_id=site.id, name="Zone A", risk_level="High")
        db.session.add(zone)
        point = Point(zone_id=zone.id, code="P-1", name="Point 1", type="Surface")
        db.session.add(point)
        plan = Plan(site_id=site.id, name="Plan A", frequency="weekly")
        db.session.add(plan)
        method = Method(code="M1", name="Method 1", unit="cfu", limit_type="Max", max_val=10)
        db.session.add(method)
        db.session.commit()
    yield app


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


@pytest.fixture()
def runner(app: Flask):
    return app.test_cli_runner()
