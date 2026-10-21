from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash

)

from ai_recommender import astar_recommend

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from extensions import db, login_manager
from models import User, Trek, Booking, StaffProfile
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///trek_manager.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route("/")
def home():

    if current_user.is_authenticated:

        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))

        elif current_user.role == "staff":
            return redirect(url_for("staff_dashboard"))

        elif current_user.role == "trekker":
            return redirect(url_for("user_dashboard"))

    open_treks = Trek.query.filter(
        Trek.status == "Open",
        Trek.available_slots > 0
    ).order_by(Trek.start_date.asc()).limit(6).all()
    return render_template("landing.html", treks=open_treks)

@app.route("/landing")
def landing():
    open_treks = Trek.query.filter(
        Trek.status == "Open",
        Trek.available_slots > 0
    ).order_by(Trek.start_date.asc()).limit(6).all()
    return render_template("landing.html", treks=open_treks)


@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register/trekker", methods=["GET", "POST"])
def trekker_register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "Email already registered.",
                "danger"
            )

            return redirect(
                url_for("trekker_register")
            )
        user = User(
            name=name,
            email=email,
            role="trekker",
            is_approved=True,
            is_blacklisted=False
        )

        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(
            "Registration successful. Please login.",
            "success"
        )
        return redirect(
            url_for("login")
        )
    return render_template(
        "trekker_register.html"
    )

@app.route("/staff/register", methods=["GET", "POST"])
def staff_register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        contact_number = request.form.get("contact_number")
        experience_years = request.form.get("experience_years")
        specialization = request.form.get("specialization")
        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "Email already registered.",
                "danger"
            )

            return redirect(
                url_for("staff_register")
            )

        staff = User(
            name=name,
            email=email,
            role="staff",
            is_approved=False,
            is_blacklisted=False
        )

        staff.set_password(password)

        db.session.add(staff)

        db.session.flush()

        profile = StaffProfile(
            user_id=staff.id,
            contact_number=contact_number,
            experience_years=experience_years,
            specialization=specialization
        )

        db.session.add(profile)

        db.session.commit()

        flash(
            "Staff registration submitted. Wait for admin approval.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "staff_register.html"
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(
            email=email
        ).first()

        if user is None:
            flash(
                "Invalid email or password.",
                "danger"
            )
            return redirect(
                url_for("login")
            )
        if not user.check_password(password):
            flash(
                "Invalid email or password.",
                "danger"
            )
            return redirect(
                url_for("login")
            )
        if user.is_blacklisted:

            flash(
                "Your account has been blacklisted.",
                "danger"
            )

            return redirect(
                url_for("login")
            )
        if user.role == "staff" and not user.is_approved:

            flash(
                "Your account is waiting for admin approval.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        login_user(user)

        if user.role == "admin":

            return redirect(
                url_for("admin_dashboard")
            )

        elif user.role == "staff":

            return redirect(
                url_for("staff_dashboard")
            )

        else:

            return redirect(
                url_for("user_dashboard")
            )
    return render_template("login.html")

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(url_for("login"))

    total_treks = Trek.query.count()

    total_users = User.query.filter_by(
        role="trekker"
    ).count()

    total_staff = User.query.filter_by(
        role="staff"
    ).count()

    total_bookings = Booking.query.count()

    return render_template(
        "admin_dashboard.html",
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings
    )

@app.route("/admin/bookings")
@login_required
def admin_bookings():

    if current_user.role != "admin":
        flash(
            "Access denied.",
            "danger"
        )
        return redirect(url_for("login"))
    bookings = Booking.query.all()
    return render_template(
        "admin_bookings.html",
        bookings=bookings
    )

@app.route("/staff/dashboard")
@login_required
def staff_dashboard():
    if current_user.role != "staff":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))
    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=current_user.id
    ).order_by(Trek.start_date.asc()).all()
    trek_data = []
    total_participants = 0
    for trek in assigned_treks:
        participant_count = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).count()
        completed_count = Booking.query.filter_by(
            trek_id=trek.id,
            status="Completed"
        ).count()
        total_participants += participant_count
        trek_data.append({
            "trek": trek,
            "participant_count": participant_count,
            "completed_count": completed_count
        })
    today = datetime.now().date()
    upcoming_count = sum(
        1 for item in trek_data
        if item["trek"].start_date
        and item["trek"].start_date >= today
        and item["trek"].status != "Completed"
    )
    completed_trek_count = sum(
        1 for item in trek_data
        if item["trek"].status == "Completed"
    )
    return render_template(
        "staff_dashboard.html",
        trek_data=trek_data,
        total_assigned=len(assigned_treks),
        total_participants=total_participants,
        upcoming_count=upcoming_count,
        completed_trek_count=completed_trek_count
    )

@app.route("/user/dashboard")
@login_required
def user_dashboard():
    if current_user.role != "trekker":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))
    bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).order_by(Booking.booking_date.desc()).all()
    open_treks = Trek.query.filter(
        Trek.status == "Open",
        Trek.available_slots > 0
    ).order_by(Trek.start_date.asc()).all()
    upcoming_bookings = [
        booking for booking in bookings
        if booking.status == "Booked"
        and booking.trek.status != "Completed"
    ]
    completed_bookings = [
        booking for booking in bookings
        if booking.status == "Completed"
        or booking.trek.status == "Completed"
    ]
    return render_template(
        "user_dashboard.html",
        treks=open_treks,
        bookings=bookings,
        upcoming_bookings=upcoming_bookings[:5],
        completed_bookings=completed_bookings[:5],
        available_count=len(open_treks),
        booking_count=len(bookings),
        upcoming_count=len(upcoming_bookings),
        completed_count=len(completed_bookings)
    )

@app.route("/user/treks")
@login_required
def available_treks():

    if current_user.role != "trekker":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    search = request.args.get("search", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()

    query = Trek.query.filter(
        Trek.status == "Open",
        Trek.available_slots > 0
    )

    if search:
        query = query.filter(
            Trek.name.ilike(f"%{search}%")
        )

    if difficulty:
        query = query.filter(
            Trek.difficulty == difficulty
        )

    if location:
        query = query.filter(
            Trek.location.ilike(f"%{location}%")
        )

    treks = query.all()

    return render_template(
        "available_treks.html",
        treks=treks,
        search=search,
        difficulty=difficulty,
        location=location
    )

@app.route("/user/trek/<int:trek_id>")
@login_required
def trek_details(trek_id):
    if current_user.role != "trekker":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))
    trek = db.session.get(Trek, trek_id)
    if trek is None:
        flash("Trek not found.", "danger")
        return redirect(url_for("available_treks"))
    existing_booking = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.trek_id == trek.id,
        Booking.status == "Booked"
    ).first()
    return render_template(
        "trek_details.html",
        trek=trek,
        existing_booking=existing_booking
    )

@app.route(
    "/user/book/<int:trek_id>",
    methods=["POST"]
)
@login_required
def book_trek(trek_id):

    if current_user.role != "trekker":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    trek = db.session.get(
        Trek,
        trek_id
    )

    if trek is None:

        flash(
            "Trek not found.",
            "danger"
        )

        return redirect(
            url_for("available_treks")
        )

    if trek.status != "Open":
        flash(
            "This trek is not currently open for booking.",
            "danger"
        )

        return redirect(
            url_for(
                "trek_details",
                trek_id=trek.id
            )
        )

    if trek.available_slots <= 0:

        flash(
            "No slots are available for this trek.",
            "danger"
        )

        return redirect(
            url_for(
                "trek_details",
                trek_id=trek.id
            )
        )

    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id,
        status="Booked"
    ).first()

    if existing_booking:
        flash(
            "You have already booked this trek.",
            "warning"
        )

        return redirect(
            url_for("my_bookings")
        )

    booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        status="Booked",
        payment_status="Pending"
    )

    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()

    flash(
        "Trek booked successfully.",
        "success"
    )

    return redirect(
        url_for("my_bookings")
    )

@app.route("/user/bookings")
@login_required
def my_bookings():

    if current_user.role != "trekker":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Booking.booking_date.desc()
    ).all()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )

@app.route(
    "/user/booking/<int:booking_id>/cancel",
    methods=["POST"]
)
@login_required
def cancel_booking(booking_id):

    if current_user.role != "trekker":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:

        flash(
            "Booking not found.",
            "danger"
        )

        return redirect(
            url_for("my_bookings")
        )

    # user cancellation feature

    if booking.user_id != current_user.id:

        flash(
            "You cannot cancel this booking.",
            "danger"
        )

        return redirect(
            url_for("my_bookings")
        )

    # No cancel for cancelled/completed booking

    if booking.status != "Booked":
        flash(
            "This booking cannot be cancelled.",
            "warning"
        )
        return redirect(url_for("my_bookings"))
    if booking.trek.status in ["Ongoing", "Completed"]:
        flash(
            "A trek that has started or completed cannot be cancelled.",
            "warning"
        )
        return redirect(url_for("my_bookings"))
    booking.status = "Cancelled"
    booking.trek.available_slots += 1
    db.session.commit()

    flash(
        "Booking cancelled successfully.",
        "success"
    )

    return redirect(
        url_for("my_bookings")
    )

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if current_user.role not in ["trekker", "staff"]:

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    staff_profile = None

    if current_user.role == "staff":

        staff_profile = StaffProfile.query.filter_by(
            user_id=current_user.id
        ).first()

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")

        if not name or not email:

            flash(
                "Name and email are required.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_user:

            flash(
                "This email is already registered.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        current_user.name = name
        current_user.email = email

        # Staff-specific profile

        if current_user.role == "staff":

            contact_number = request.form.get(
                "contact_number"
            )

            experience_years = request.form.get(
                "experience_years"
            )

            specialization = request.form.get(
                "specialization"
            )

            try:

                experience_years = int(
                    experience_years
                )

            except (TypeError, ValueError):

                flash(
                    "Experience must be a valid number.",
                    "danger"
                )

                return redirect(
                    url_for("profile")
                )

            if experience_years < 0:

                flash(
                    "Experience cannot be negative.",
                    "danger"
                )

                return redirect(
                    url_for("profile")
                )

            if staff_profile:

                staff_profile.contact_number = contact_number
                staff_profile.experience_years = experience_years
                staff_profile.specialization = specialization

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    return render_template(
        "profile.html",
        staff_profile=staff_profile
    )

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("login")
    )

def create_default_admin():

    admin = User.query.filter_by(
        email=os.getenv("ADMIN_EMAIL")
    ).first()

    if admin is None:

        admin = User(
            name="System Admin",
            email=os.getenv("ADMIN_EMAIL"),
            role="admin",
            is_approved=True,
            is_blacklisted=False
        )

        admin.set_password(os.getenv("ADMIN_PASSWORD"))

        db.session.add(admin)
        db.session.commit()

        print("Default admin created successfully.")

    else:
        print("Default admin already exists.")

@app.route("/admin/create-trek", methods=["GET", "POST"])
@login_required
def create_trek():
    total_slots = request.form.get("total_slots")
    difficulty = request.form.get("difficulty")

    if current_user.role != "admin":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    if request.method == "POST":
        name = request.form.get("name")
        location = request.form.get("location")
        duration = request.form.get("duration")
        available_slots = request.form.get("available_slots")
        difficulty = request.form.get("difficulty")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        start_date = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

        end_date = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()
        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=int(duration),
            total_slots=int(total_slots),
            available_slots=int(total_slots),
            start_date=start_date,
            end_date=end_date
        )

        db.session.add(trek)
        db.session.commit()

        flash(
            "Trek created successfully.",
            "success"
        )

        return redirect(
            url_for("admin_treks")
        )

    return render_template(
        "create_trek.html"
    )

@app.route("/admin/treks")
@login_required
def admin_treks():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    query = Trek.query

    if search:

        if search.isdigit():

            query = query.filter(
                Trek.id == int(search)
            )

        else:

            query = query.filter(
                Trek.name.ilike(f"%{search}%")
            )

    treks = query.order_by(
        Trek.id.desc()
    ).all()

    staff_members = User.query.filter_by(
        role="staff",
        is_approved=True,
        is_blacklisted=False
    ).all()

    return render_template(
        "admin_treks.html",
        treks=treks,
        staff_members=staff_members,
        search=search
    )

@app.route("/admin/staff")
@login_required
def admin_staff():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    query = User.query.filter_by(
        role="staff"
    )

    if search:

        if search.isdigit():

            query = query.filter(
                User.id == int(search)
            )

        else:

            query = query.filter(
                User.name.ilike(f"%{search}%")
            )

    staff_members = query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "admin_staff.html",
        staff_members=staff_members,
        search=search
    )

@app.route("/admin/users")
@login_required
def admin_users():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()

    query = User.query.filter(
        User.role == "trekker"
    )

    if search:
        if search.isdigit():
            query = query.filter(
                User.id == int(search)
            )
        else:
            query = query.filter(
                User.name.ilike(f"%{search}%")
            )

    users = query.order_by(User.id.desc()).all()

    return render_template(
        "admin_users.html",
        users=users,
        search=search
    )

@app.route(
    "/admin/users/blacklist/<int:user_id>",
    methods=["POST"]
)
@login_required
def blacklist_user(user_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    user = db.session.get(User, user_id)

    if user is None or user.role != "trekker":
        flash("User not found.", "danger")
        return redirect(url_for("admin_users"))

    user.is_blacklisted = True

    db.session.commit()

    flash(
        f"{user.name} has been blacklisted.",
        "warning"
    )

    return redirect(url_for("admin_users"))

@app.route(
    "/admin/users/unblacklist/<int:user_id>",
    methods=["POST"]
)
@login_required
def unblacklist_user(user_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    user = db.session.get(User, user_id)

    if user is None or user.role != "trekker":
        flash("User not found.", "danger")
        return redirect(url_for("admin_users"))

    user.is_blacklisted = False

    db.session.commit()

    flash(
        f"{user.name} has been removed from the blacklist.",
        "success"
    )

    return redirect(url_for("admin_users"))

@app.route("/admin/edit-trek/<int:trek_id>", methods=["GET", "POST"])
@login_required
def edit_trek(trek_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    trek = db.session.get(Trek, trek_id)

    if trek is None:
        flash("Trek not found.", "danger")
        return redirect(url_for("admin_treks"))

    if request.method == "POST":

        trek.name = request.form.get("name")
        trek.location = request.form.get("location")
        trek.difficulty = request.form.get("difficulty")

        trek.duration = int(request.form.get("duration"))
        trek.total_slots = int(request.form.get("total_slots"))

        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        trek.start_date = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

        trek.end_date = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()

        db.session.commit()

        flash("Trek updated successfully.", "success")

        return redirect(
            url_for("admin_treks")
        )

    return render_template(
        "edit_trek.html",
        trek=trek
    )

@app.route("/admin/delete-trek/<int:trek_id>", methods=["POST"])
@login_required
def delete_trek(trek_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    trek = db.session.get(Trek, trek_id)

    if trek is None:
        flash("Trek not found.", "danger")
        return redirect(url_for("admin_treks"))

    # No deletion if someone already booked
    booking_count = Booking.query.filter_by(
        trek_id=trek.id
    ).count()

    if booking_count > 0:
        flash(
            "This trek cannot be deleted because it has booking history.",
            "warning"
        )
        return redirect(url_for("admin_treks"))

    db.session.delete(trek)
    db.session.commit()

    flash(
        "Trek deleted successfully.",
        "success"
    )

    return redirect(url_for("admin_treks"))

@app.route("/admin/staff/approve/<int:staff_id>", methods=["POST"])
@login_required
def approve_staff(staff_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    staff = db.session.get(User, staff_id)

    if staff is None or staff.role != "staff":
        flash("Staff member not found.", "danger")
        return redirect(url_for("admin_staff"))

    staff.is_approved = True

    db.session.commit()

    flash(
        f"{staff.name} has been approved successfully.",
        "success"
    )

    return redirect(url_for("admin_staff"))

@app.route("/admin/staff/blacklist/<int:staff_id>", methods=["POST"])
@login_required
def blacklist_staff(staff_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    staff = db.session.get(User, staff_id)

    if staff is None or staff.role != "staff":
        flash("Staff member not found.", "danger")
        return redirect(url_for("admin_staff"))

    staff.is_blacklisted = True

    db.session.commit()

    flash(
        f"{staff.name} has been blacklisted.",
        "warning"
    )

    return redirect(url_for("admin_staff"))

@app.route("/admin/staff/unblacklist/<int:staff_id>", methods=["POST"])
@login_required
def unblacklist_staff(staff_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    staff = db.session.get(User, staff_id)

    if staff is None or staff.role != "staff":
        flash("Staff member not found.", "danger")
        return redirect(url_for("admin_staff"))

    staff.is_blacklisted = False

    db.session.commit()

    flash(
        f"{staff.name} has been removed from the blacklist.",
        "success"
    )

    return redirect(url_for("admin_staff"))

@app.route(
    "/admin/trek/<int:trek_id>/assign-staff",
    methods=["POST"]
)
@login_required
def assign_staff(trek_id):

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    trek = db.session.get(Trek, trek_id)

    if trek is None:
        flash("Trek not found.", "danger")
        return redirect(url_for("admin_treks"))

    staff_id = request.form.get("staff_id")

    staff = db.session.get(User, int(staff_id))

    if staff is None or staff.role != "staff":
        flash("Invalid staff member.", "danger")
        return redirect(url_for("admin_treks"))

    if not staff.is_approved or staff.is_blacklisted:
        flash(
            "Only approved active staff can be assigned.",
            "danger"
        )
        return redirect(url_for("admin_treks"))

    trek.assigned_staff_id = staff.id

    db.session.commit()

    flash(
        f"{staff.name} assigned to {trek.name}.",
        "success"
    )

    return redirect(url_for("admin_treks"))

@app.route("/staff/trek/<int:trek_id>")
@login_required
def staff_trek_details(trek_id):

    if current_user.role != "staff":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(url_for("login"))

    trek = db.session.get(
        Trek,
        trek_id
    )

    if trek is None:

        flash(
            "Trek not found.",
            "danger"
        )

        return redirect(
            url_for("staff_dashboard")
        )

    if trek.assigned_staff_id != current_user.id:

        flash(
            "You are not assigned to this trek.",
            "danger"
        )

        return redirect(
            url_for("staff_dashboard")
        )

    bookings = Booking.query.filter_by(
        trek_id=trek.id
    ).all()

    return render_template(
        "staff_trek_details.html",
        trek=trek,
        bookings=bookings
    )

@app.route(
    "/staff/trek/<int:trek_id>/update-status",
    methods=["POST"]
)
@login_required
def update_trek_status(trek_id):

    if current_user.role != "staff":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    trek = db.session.get(
        Trek,
        trek_id
    )

    if trek is None:

        flash(
            "Trek not found.",
            "danger"
        )

        return redirect(
            url_for("staff_dashboard")
        )

    # Only assigned staff can modify this trek

    if trek.assigned_staff_id != current_user.id:

        flash(
            "You are not assigned to this trek.",
            "danger"
        )

        return redirect(
            url_for("staff_dashboard")
        )

    status = request.form.get("status")

    allowed_statuses = [
        "Pending",
        "Approved",
        "Open",
        "Closed",
        "Ongoing",
        "Completed"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid trek status.",
            "danger"
        )

        return redirect(
            url_for(
                "staff_trek_details",
                trek_id=trek.id
            )
        )

    trek.status = status

    if status == "Completed":

        bookings = Booking.query.filter_by(
            trek_id=trek.id,
            status="Booked"
        ).all()

        for booking in bookings:
            booking.status = "Completed"

    db.session.commit()

    flash(
        "Trek status updated successfully.",
        "success"
    )

    return redirect(
        url_for(
            "staff_trek_details",
            trek_id=trek.id
        )
    )

@app.route(
    "/staff/trek/<int:trek_id>/update-slots",
    methods=["POST"]
)
@login_required
def update_trek_slots(trek_id):
    if current_user.role != "staff":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))
    trek = db.session.get(Trek, trek_id)
    if trek is None:
        flash("Trek not found.", "danger")
        return redirect(url_for("staff_dashboard"))
    if trek.assigned_staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff_dashboard"))
    try:
        total_slots = int(request.form.get("total_slots"))
    except (TypeError, ValueError):
        flash("Total slots must be a valid number.", "danger")
        return redirect(url_for("staff_trek_details", trek_id=trek.id))
    booked_count = Booking.query.filter_by(
        trek_id=trek.id,
        status="Booked"
    ).count()
    if total_slots < 1:
        flash("Total slots must be at least 1.", "danger")
        return redirect(url_for("staff_trek_details", trek_id=trek.id))
    if total_slots < booked_count:
        flash(
            f"Total slots cannot be less than the {booked_count} active bookings.",
            "danger"
        )
        return redirect(url_for("staff_trek_details", trek_id=trek.id))
    trek.total_slots = total_slots
    trek.available_slots = total_slots - booked_count
    db.session.commit()
    flash("Trek capacity updated successfully.", "success")
    return redirect(url_for("staff_trek_details", trek_id=trek.id))
@app.route(
    "/staff/booking/<int:booking_id>/status",
    methods=["POST"]
)
@login_required
def update_participant_status(booking_id):
    if current_user.role != "staff":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))
    booking = db.session.get(Booking, booking_id)
    if booking is None:
        flash("Booking not found.", "danger")
        return redirect(url_for("staff_dashboard"))
    if booking.trek.assigned_staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for("staff_dashboard"))
    new_status = request.form.get("status")
    if booking.status == "Booked" and new_status == "Completed":
        booking.status = "Completed"
    elif booking.status == "Booked" and new_status == "Cancelled":
        booking.status = "Cancelled"
        if booking.trek.available_slots < booking.trek.total_slots:
            booking.trek.available_slots += 1
    else:
        flash(
            "Invalid participant status change.",
            "danger"
        )
        return redirect(
            url_for(
                "staff_trek_details",
                trek_id=booking.trek_id
            )
        )
    db.session.commit()
    flash(
        "Participant booking updated successfully.",
        "success"
    )
    return redirect(
        url_for(
            "staff_trek_details",
            trek_id=booking.trek_id
        )
    )


@app.route("/user/ai-recommendations", methods=["GET", "POST"])
@login_required
def ai_recommendations():
    if current_user.role != "trekker":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    recommendations = None
    preferences = {
        "location": "",
        "difficulty": "Moderate",
        "max_duration": 2,
    }

    if request.method == "POST":
        location = request.form.get("location", "").strip()
        difficulty = request.form.get("difficulty", "Moderate").strip()
        max_duration_raw = request.form.get("max_duration", "2")

        if not location:
            flash("Please enter a preferred location.", "danger")
        else:
            try:
                max_duration = int(max_duration_raw)

                if max_duration < 1:
                    raise ValueError

                preferences = {
                    "location": location,
                    "difficulty": difficulty,
                    "max_duration": max_duration,
                }

                treks = Trek.query.all()

                trek_data = [
                    {
                        "id": trek.id,
                        "name": trek.name,
                        "location": trek.location,
                        "difficulty": trek.difficulty,
                        "duration": trek.duration,
                        "status": trek.status,
                        "available_slots": trek.available_slots,
                    }
                    for trek in treks
                ]

                result = astar_recommend(trek_data, preferences)
                recommendations = result

            except ValueError:
                flash("Maximum duration must be a positive whole number.", "danger")

    return render_template(
        "ai_recommendations.html",
        recommendations=recommendations,
        preferences=preferences,
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_default_admin()

    app.run(debug=True)