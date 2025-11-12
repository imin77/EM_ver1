from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DateTimeLocalField,
    FloatField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SiteForm(FlaskForm):
    name = StringField("Site Name", validators=[DataRequired()])
    submit = SubmitField("Add Site")


class ZoneForm(FlaskForm):
    site_id = SelectField("Site", coerce=int, validators=[DataRequired()])
    name = StringField("Zone Name", validators=[DataRequired()])
    risk_level = SelectField(
        "Risk Level",
        choices=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add Zone")


class PointForm(FlaskForm):
    zone_id = SelectField("Zone", coerce=int, validators=[DataRequired()])
    code = StringField("Code", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    type = SelectField(
        "Type",
        choices=[("Surface", "Surface"), ("Air", "Air"), ("Water", "Water"), ("Swab", "Swab")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add Point")


class PlanForm(FlaskForm):
    site_id = SelectField("Site", coerce=int, validators=[DataRequired()])
    name = StringField("Plan Name", validators=[DataRequired()])
    frequency = SelectField(
        "Frequency",
        choices=[("weekly", "Weekly"), ("monthly", "Monthly")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Create Plan")


class ScheduleGenerateForm(FlaskForm):
    plan_id = SelectField("Plan", coerce=int, validators=[DataRequired()])
    start_date = DateField("Start Date", default=date.today, validators=[DataRequired()])
    periods = SelectField(
        "Periods",
        choices=[(4, "4"), (8, "8"), (12, "12")],
        coerce=int,
        validators=[DataRequired()],
    )
    submit = SubmitField("Generate")


class SampleForm(FlaskForm):
    schedule_id = SelectField("Schedule", coerce=int, validators=[DataRequired()])
    collected_at = DateTimeLocalField("Collected At", format="%Y-%m-%dT%H:%M", validators=[Optional()])
    collected_by = StringField("Collected By", validators=[Optional()])
    note = TextAreaField("Note", validators=[Optional()])
    submit = SubmitField("Register Sample")


class TestOrderForm(FlaskForm):
    sample_id = SelectField("Sample", coerce=int, validators=[DataRequired()])
    method_id = SelectField("Method", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Create Test Order")


class TestResultForm(FlaskForm):
    order_id = SelectField("Order", coerce=int, validators=[DataRequired()])
    value = FloatField("Value", validators=[Optional()])
    unit = StringField("Unit", validators=[Optional()])
    qual = StringField("Qualitative", validators=[Optional()])
    submit = SubmitField("Submit Result")
