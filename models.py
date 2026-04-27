from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# 👮 USER MODEL (FIXED)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default="officer")


# 🚓 VIOLATION MODEL
class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    vehicle_number = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    violation_type = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)

    fine_amount = db.Column(db.Integer, nullable=False)

    image = db.Column(db.String(200), nullable=True)

    status = db.Column(db.String(20), default="Unpaid")