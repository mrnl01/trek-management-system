from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="trekker"
    )

    is_approved = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    is_blacklisted = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

class Trek(db.Model):
    __tablename__ = "treks"
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String(150),
        nullable=False
    )
    location = db.Column(
        db.String(150),
        nullable=False
    )
    difficulty = db.Column(
        db.String(20),
        nullable=False
    )
    duration = db.Column(
        db.Integer,
        nullable=False
    )
    total_slots = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    available_slots = db.Column(
        db.Integer,
        nullable=False
    )
    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )
    assigned_staff = db.relationship(
        "User",
        backref="assigned_treks"
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )
    start_date = db.Column(
        db.Date,
        nullable=False
    )
    end_date = db.Column(
        db.Date,
        nullable=False
    )

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    trek_id = db.Column(
        db.Integer,
        db.ForeignKey("treks.id"),
        nullable=False
    )
    booking_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default="Booked"
    )
    payment_status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )
    user = db.relationship(
        "User",
        backref="bookings"
    )

    trek = db.relationship(
        "Trek",
        backref="bookings"
    )
class StaffProfile(db.Model):
    __tablename__ = "staff_profiles"
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )
    contact_number = db.Column(
        db.String(20),
        nullable=False
    )
    experience_years = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )
    specialization = db.Column(
        db.String(150),
        nullable=True
    )
    user = db.relationship(
        "User",
        backref=db.backref(
            "staff_profile",
            uselist=False
        )
    )
