from . import db
from flask_login import UserMixin
from sqlalchemy.dialects.sqlite import JSON  # use JSON for SQLite; change if using PostgreSQL

# -------------------
# User model
# -------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

    # Relationship to Tasting entries
    tastings = db.relationship('Tasting', backref='user', lazy=True)


# -------------------
# Tasting model
# -------------------
class Tasting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    store_name = db.Column(db.String(150), nullable=False)

    # Store all products and their sold/on-hand/left info in a JSON column
    products = db.Column(JSON, default={})  # e.g., {"Pure Blue Vodka": {"to_sell": 5, "sold": 2, "left": 3}}

    # Sales tracking
    bottles_to_sell = db.Column(db.Integer, default=0)
    bottles_sold = db.Column(db.Integer, default=0)
    bottles_left = db.Column(db.Integer, default=0)
    total_bottles = db.Column(db.Integer, default=0)
    poured_to_sold_percent = db.Column(db.Float, default=0.0)
    tastings_poured = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
