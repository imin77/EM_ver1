from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()


class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    zones = db.relationship("Zone", backref="site", lazy=True)
    plans = db.relationship("Plan", backref="site", lazy=True)


class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("site.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    risk_level = db.Column(db.String(10))
    points = db.relationship("Point", backref="zone", lazy=True)


class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("zone.id"), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20))
    schedules = db.relationship("Schedule", backref="point", lazy=True)


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("site.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    schedules = db.relationship("Schedule", backref="plan", lazy=True)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("plan.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False)
    status = db.Column(db.String(12), default="Planned")
    sample = db.relationship("Sample", backref="schedule", uselist=False)


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"), nullable=False)
    collected_at = db.Column(db.DateTime)
    collected_by = db.Column(db.String(50))
    note = db.Column(db.Text)
    orders = db.relationship("TestOrder", backref="sample", lazy=True)


class Method(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(30))
    limit_type = db.Column(db.String(16))
    min_val = db.Column(db.Float)
    max_val = db.Column(db.Float)
    orders = db.relationship("TestOrder", backref="method", lazy=True)


class TestOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("sample.id"), nullable=False)
    method_id = db.Column(db.Integer, db.ForeignKey("method.id"), nullable=False)
    status = db.Column(db.String(12), default="Requested")
    result = db.relationship("TestResult", backref="order", uselist=False)


class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("test_order.id"), nullable=False)
    value = db.Column(db.Float)
    unit = db.Column(db.String(30))
    qual = db.Column(db.String(20))
    judged = db.Column(db.String(12))
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pw_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), default="Viewer")

    def get_id(self):
        return str(self.id)
