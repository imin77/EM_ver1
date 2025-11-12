from __future__ import annotations

import csv
import os
from datetime import datetime, date
from io import StringIO
from pathlib import Path

from flask import (
    Flask,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash

from forms import (
    LoginForm,
    PlanForm,
    PointForm,
    SampleForm,
    ScheduleGenerateForm,
    SiteForm,
    TestOrderForm,
    TestResultForm,
    ZoneForm,
)
from models import (
    Method,
    Plan,
    Point,
    Sample,
    Schedule,
    Site,
    TestOrder,
    TestResult,
    User,
    Zone,
    db,
)
from services.judge import judge
from services.schedule import generate as generate_schedule


BASE_DIR = Path(__file__).resolve().parent


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///" + str(BASE_DIR / "instance" / "em.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    def seed_defaults() -> bool:
        """Ensure critical seed data exists. Returns True if anything was created."""
        created = False
        if not User.query.filter_by(email="admin@example.com").first():
            user = User(
                email="admin@example.com",
                pw_hash=generate_password_hash("admin"),
                role="Admin",
            )
            db.session.add(user)
            created = True
        if not Site.query.first():
            site = Site(name="Seoul Plant")
            db.session.add(site)
            db.session.flush()
            zone = Zone(site_id=site.id, name="Packaging", risk_level="High")
            db.session.add(zone)
            point = Point(zone_id=zone.id, code="PKG-01", name="Conveyor Belt", type="Surface")
            db.session.add(point)
            created = True
        if not Method.query.first():
            method = Method(
                code="TBC",
                name="Total Bacterial Count",
                unit="CFU/25cm2",
                limit_type="Max",
                max_val=10,
            )
            db.session.add(method)
            created = True
        if created:
            db.session.commit()
        return created

    @app.route("/init")
    def init_app():
        db.create_all()
        created = seed_defaults()
        if created:
            flash(
                "Database initialized with default admin (admin@example.com / admin)",
                "success",
            )
        else:
            flash("Database already initialized", "info")
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("index"))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.pw_hash, form.password.data):
                login_user(user)
                return redirect(url_for("index"))
            flash("Invalid credentials", "danger")
        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    def require_roles(*roles):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if current_user.role not in roles:
                    flash("You do not have permission to perform this action.", "warning")
                    return redirect(request.referrer or url_for("index"))
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            return login_required(wrapper)

        return decorator

    with app.app_context():
        db.create_all()
        seed_defaults()

    @app.route("/")
    @login_required
    def index():
        today = date.today()
        month_start = date(today.year, today.month, 1)
        results = (
            TestResult.query.join(TestOrder)
            .filter(TestResult.reported_at >= month_start)
            .with_entities(TestResult.judged, db.func.count(TestResult.id))
            .group_by(TestResult.judged)
            .all()
        )
        counts = {"Pass": 0, "Fail": 0, "Review": 0}
        for judged, count in results:
            if judged in counts:
                counts[judged] = count
        recent_orders = (
            TestOrder.query.order_by(TestOrder.id.desc()).limit(5).all()
        )
        return render_template("index.html", counts=counts, recent_orders=recent_orders)

    @app.route("/points", methods=["GET", "POST"])
    @login_required
    def points():
        site_form = SiteForm()
        zone_form = ZoneForm()
        point_form = PointForm()
        site_form.submit.label.text = "Add Site"
        zone_form.site_id.choices = [(s.id, s.name) for s in Site.query.all()]
        point_form.zone_id.choices = [(z.id, f"{z.site.name} - {z.name}") for z in Zone.query.all()]

        if site_form.validate_on_submit() and site_form.submit.data:
            site = Site(name=site_form.name.data)
            db.session.add(site)
            db.session.commit()
            flash("Site created", "success")
            return redirect(url_for("points"))

        if zone_form.validate_on_submit() and zone_form.submit.data:
            zone = Zone(site_id=zone_form.site_id.data, name=zone_form.name.data, risk_level=zone_form.risk_level.data)
            db.session.add(zone)
            db.session.commit()
            flash("Zone created", "success")
            return redirect(url_for("points"))

        if point_form.validate_on_submit() and point_form.submit.data:
            point = Point(
                zone_id=point_form.zone_id.data,
                code=point_form.code.data,
                name=point_form.name.data,
                type=point_form.type.data,
            )
            db.session.add(point)
            db.session.commit()
            flash("Point created", "success")
            return redirect(url_for("points"))

        points = Point.query.all()
        return render_template(
            "points.html",
            points=points,
            site_form=site_form,
            zone_form=zone_form,
            point_form=point_form,
        )

    @app.route("/plans", methods=["GET", "POST"])
    @login_required
    def plans():
        form = PlanForm()
        form.site_id.choices = [(s.id, s.name) for s in Site.query.all()]
        if form.validate_on_submit():
            plan = Plan(site_id=form.site_id.data, name=form.name.data, frequency=form.frequency.data)
            db.session.add(plan)
            db.session.commit()
            flash("Plan created", "success")
            return redirect(url_for("plans"))
        plans = Plan.query.all()
        schedule_form = ScheduleGenerateForm()
        schedule_form.plan_id.choices = [(p.id, p.name) for p in plans]
        return render_template("plans.html", form=form, plans=plans, schedule_form=schedule_form)

    @app.route("/schedules/generate", methods=["POST"])
    @login_required
    def generate_schedules():
        form = ScheduleGenerateForm()
        form.plan_id.choices = [(p.id, p.name) for p in Plan.query.all()]
        if form.validate_on_submit():
            plan = Plan.query.get(form.plan_id.data)
            if not plan:
                flash("Plan not found", "danger")
                return redirect(url_for("plans"))
            created = generate_schedule(plan, form.start_date.data, form.periods.data)
            flash(f"Generated {len(created)} schedules", "success")
        else:
            flash("Failed to generate schedules", "danger")
        return redirect(url_for("plans"))

    @app.route("/samples", methods=["GET", "POST"])
    @login_required
    def samples():
        form = SampleForm()
        form.schedule_id.choices = [
            (s.id, f"{s.date} - {s.point.code}")
            for s in Schedule.query.order_by(Schedule.date.desc()).all()
        ]
        order_form = TestOrderForm()
        order_form.sample_id.choices = [(s.id, f"Sample {s.id}") for s in Sample.query.all()]
        order_form.method_id.choices = [(m.id, m.name) for m in Method.query.all()]
        if form.validate_on_submit():
            schedule = Schedule.query.get(form.schedule_id.data)
            if not schedule:
                flash("Schedule not found", "danger")
                return redirect(url_for("samples"))
            sample = Sample(
                schedule_id=schedule.id,
                collected_at=form.collected_at.data,
                collected_by=form.collected_by.data,
                note=form.note.data,
            )
            schedule.status = "Collected"
            db.session.add(sample)
            db.session.commit()
            flash("Sample registered", "success")
            return redirect(url_for("samples"))
        samples = Sample.query.order_by(Sample.id.desc()).all()
        schedules = Schedule.query.order_by(Schedule.date.desc()).all()
        return render_template(
            "samples.html",
            form=form,
            order_form=order_form,
            samples=samples,
            schedules=schedules,
        )

    @app.route("/test-orders", methods=["POST"])
    @login_required
    def test_orders():
        form = TestOrderForm()
        form.sample_id.choices = [(s.id, f"Sample {s.id}") for s in Sample.query.all()]
        form.method_id.choices = [(m.id, m.name) for m in Method.query.all()]
        if form.validate_on_submit():
            order = TestOrder(sample_id=form.sample_id.data, method_id=form.method_id.data)
            db.session.add(order)
            db.session.commit()
            flash("Test order created", "success")
        else:
            flash("Failed to create test order", "danger")
        return redirect(url_for("samples"))

    @app.route("/test-results", methods=["GET", "POST"])
    @login_required
    def test_results():
        form = TestResultForm()
        orders = TestOrder.query.all()
        form.order_id.choices = [(o.id, f"Order {o.id} - {o.method.name}") for o in orders]
        if form.validate_on_submit():
            order = TestOrder.query.get(form.order_id.data)
            if not order:
                flash("Order not found", "danger")
                return redirect(url_for("test_results"))
            result = order.result
            if not result:
                result = TestResult(order_id=order.id)
            result.value = form.value.data
            result.unit = form.unit.data or order.method.unit
            result.qual = form.qual.data
            result.judged = judge(result.value, result.qual, order.method)
            order.status = "Completed"
            db.session.add(result)
            db.session.commit()
            flash("Result saved", "success")
            return redirect(url_for("test_results"))
        results = TestResult.query.order_by(TestResult.reported_at.desc()).all()
        return render_template("results.html", form=form, results=results)

    @app.route("/reports/monthly.csv")
    @login_required
    def monthly_report():
        today = date.today()
        month_start = date(today.year, today.month, 1)
        data = (
            TestResult.query.join(TestOrder)
            .join(TestOrder.sample)
            .join(Sample.schedule)
            .join(Schedule.point)
            .join(Point.zone)
            .join(Zone.site)
            .filter(TestResult.reported_at >= month_start)
            .with_entities(
                Site.name.label("site"),
                Zone.name.label("zone"),
                Point.code,
                Schedule.date,
                TestResult.value,
                TestResult.qual,
                TestResult.judged,
            )
            .all()
        )
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Site", "Zone", "Point", "Schedule Date", "Value", "Qual", "Judged"])
        for row in data:
            writer.writerow(row)
        output.seek(0)
        return Response(
            output.read(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=monthly_report.csv"},
        )

    @app.route("/trends/series")
    @login_required
    def trend_series():
        point_id = request.args.get("point_id", type=int)
        method_id = request.args.get("method_id", type=int)
        query = TestResult.query.join(TestOrder).join(TestOrder.sample).join(Sample.schedule)
        if point_id:
            query = query.filter(Schedule.point_id == point_id)
        if method_id:
            query = query.filter(TestOrder.method_id == method_id)
        results = query.order_by(TestResult.reported_at.asc()).all()
        series = [
            {
                "reported_at": r.reported_at.isoformat() if r.reported_at else None,
                "value": r.value,
                "qual": r.qual,
                "judged": r.judged,
                "order_id": r.order_id,
            }
            for r in results
        ]
        return jsonify(series)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
