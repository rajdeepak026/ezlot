from flask import Flask, render_template, redirect, request, session, url_for
from flask import current_app as app
from datetime import datetime
from .models import *
from jinja2 import Environment

app.jinja_env.filters['duration'] = lambda timedelta: str(timedelta).split('.')[0]

# Authentication Routes

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        this_user = User.query.filter_by(email=email).first()

        if this_user and this_user.pwd == pwd:
            if this_user.type == "admin":
                return redirect("/admin")
            return redirect(url_for("user_dash", user_id=this_user.id))
        return "Invalid credentials"
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        fullname = request.form.get("fullname")
        address = request.form.get("address")
        pincode = request.form.get("pincode")

        if User.query.filter_by(email=email).first():
            return "User already exists"

        new_user = User(email=email, pwd=pwd, fullname=fullname, address=address, pincode=pincode)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")


@app.route("/logout")
def logout():
    return redirect("/login")


# Admin Dashboard Routes

@app.route("/admin")
def admin_dash():
    this_user = User.query.filter_by(type="admin").first()
    all_info = Info.query.all()
    return render_template("admin_dash.html", this_user=this_user, all_info=all_info)


# User Dashboard Routes

@app.route("/user/<int:user_id>")
def user_dash(user_id):
    this_user = User.query.get_or_404(user_id)
    available_parking_lots = Info.query.filter_by(status="available").all()
    booked_lots = Info.query.filter_by(user_id=user_id, status="booked").all()
    return render_template("user_dash.html", this_user=this_user, booked_lots=booked_lots, available_parking_lots=available_parking_lots)


# Parking Lot Management Routes

@app.route("/add_lot", methods=["GET", "POST"])
def add_lot():
    if request.method == "POST":
        location = request.form.get("location")
        address = request.form.get("address")
        pincode = request.form.get("pincode")
        price = request.form.get("price")
        maxispot = request.form.get("maxispot")

        admin_user = User.query.filter_by(type="admin").first()

        new_lot = Info(
            parking=f"{location}_lot",
            status="available",
            location=location,
            address=address,
            pincode=pincode,
            price=price,
            maxispot=maxispot,
            user_id=admin_user.id
        )
        db.session.add(new_lot)
        db.session.commit()
        return redirect("/admin")

    return render_template("add_lot.html")


@app.route("/edit_parking/<parking_id>", methods=["GET", "POST"])
def edit_parking(parking_id):
    parking_lot = Info.query.filter_by(id=parking_id).first()
    if not parking_lot:
        return "Parking lot not found", 404

    if 'user_type' in session and session['user_type'] != 'admin':
        return redirect("/user")

    if request.method == "POST":
        parking_lot.parking = request.form.get("parking")
        parking_lot.status = request.form.get("status")
        parking_lot.location = request.form.get("location")
        parking_lot.address = request.form.get("address")
        parking_lot.pincode = request.form.get("pincode")
        parking_lot.price = request.form.get("price")
        parking_lot.maxispot = request.form.get("maxispot")
        db.session.commit()
        return redirect("/admin")

    return render_template("edit_parking.html", parking_lot=parking_lot)


@app.route("/delete_parking/<parking_id>", methods=["POST"])
def delete_parking(parking_id):
    parking_lot = Info.query.filter_by(id=parking_id).first()
    if not parking_lot:
        return "Parking lot not found", 404

    if parking_lot.status.lower() != "available":
        return "Cannot delete an occupied parking lot", 400

    db.session.delete(parking_lot)
    db.session.commit()
    return redirect("/admin")


@app.route("/delete_spot/<int:parking_id>", methods=["POST"])
def delete_spot(parking_id):
    parking_lot = Info.query.get_or_404(parking_id)
    db.session.delete(parking_lot)
    db.session.commit()
    return redirect("/admin")


# Booking & Releasing Routes

@app.route("/book/<int:parking_id>", methods=["GET", "POST"])
def book(parking_id):
    user_id = request.args.get("user_id")
    if not user_id:
        return "User ID missing in request", 400

    parking_lot = Info.query.get_or_404(parking_id)

    if request.method == "POST":
        vehicle_no = request.form.get("vehicle_no")
        parking_lot.status = "booked"
        parking_lot.vehicle_no = vehicle_no
        parking_lot.timestamp = datetime.now()
        parking_lot.user_id = user_id
        db.session.commit()
        return redirect(url_for("user_dash", user_id=user_id))

    return render_template("book.html", parking_lot=parking_lot, user_id=user_id)


@app.route("/release/<int:parking_id>/<int:user_id>")
def release_parking(parking_id, user_id):
    parking_lot = Info.query.get_or_404(parking_id)
    parking_lot.status = "available"
    parking_lot.vehicle_no = None
    parking_lot.timestamp = None
    db.session.commit()
    return redirect(url_for("user_dash", user_id=user_id))


@app.route("/park_out/<int:parking_id>/<int:user_id>")
def park_out(parking_id, user_id):
    parking_lot = Info.query.get_or_404(parking_id)
    now = datetime.now()

    if parking_lot.timestamp:
        time_diff = now - parking_lot.timestamp
        hours = max(1, int(time_diff.total_seconds() // 3600))
        cost = hours * int(parking_lot.price)
    else:
        hours = 0
        cost = 0

    return render_template("release.html", parking_lot=parking_lot, user_id=user_id, now=now.strftime('%Y-%m-%d %H:%M'), total_cost=cost)


@app.route("/confirm_release/<int:parking_id>/<int:user_id>", methods=["POST"])
def confirm_release(parking_id, user_id):
    parking_lot = Info.query.get_or_404(parking_id)

    if parking_lot.timestamp:
        duration = datetime.now() - parking_lot.timestamp
        total_cost = round((duration.total_seconds() / 3600) * float(parking_lot.price), 2)
    else:
        total_cost = 0

    parking_lot.status = "available"
    parking_lot.vehicle_no = None
    parking_lot.timestamp = None
    db.session.commit()

    return redirect(url_for("user_dash", user_id=user_id))


# Parking Spot Detail View

@app.route("/parking_spot/<int:parking_id>")
def parking_spot(parking_id):
    parking_spot = Info.query.get_or_404(parking_id)
    now = datetime.now()

    if parking_spot.status == "booked":
        booked_user = User.query.get(parking_spot.user_id)

        try:
            price = float(parking_spot.price or 0)
        except (ValueError, TypeError):
            price = 0

        if parking_spot.timestamp:
            duration = now - parking_spot.timestamp
            cost = (duration.total_seconds() / 3600) * price
            duration_str = format_duration(duration)
            cost_str = f"₹{cost:.2f}"
        else:
            duration_str = "N/A"
            cost_str = "N/A"

        return render_template("occupied.html",
                               parking_spot=parking_spot,
                               booked_user=booked_user,
                               this_user=booked_user,
                               parked_since=parking_spot.timestamp.strftime('%Y-%m-%d %H:%M') if parking_spot.timestamp else "N/A",
                               duration=duration_str,
                               cost=cost_str)

    admin_user = User.query.filter_by(type="admin").first()
    return render_template("parking_spot.html", parking_spot=parking_spot, this_user=admin_user)


def format_duration(timedelta):
    total_seconds = int(timedelta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"


# Additional Routes

@app.route("/view_status")
def view_status():
    return render_template("view_status.html")


@app.route("/release")
def release():
    return render_template("release.html")


@app.route("/users")
def users():
    this_user = User.query.filter_by(type="admin").first()
    all_info = Info.query.all()
    all_users = User.query.with_entities(User.id, User.email, User.fullname, User.address, User.pincode, User.type).all()
    return render_template("users.html", users=all_users, this_user=this_user, all_info=all_info)


@app.route("/search_parking", methods=["GET", "POST"])
def search_parking():
    location = request.args.get('location', '')
    price = request.args.get('price', type=float)
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    query = Info.query
    if location:
        query = query.filter(Info.location.ilike(f"%{location}%"))
    if price:
        query = query.filter(Info.price <= price)
    if status:
        query = query.filter(Info.status == status)

    parking_lots = query.paginate(page=page, per_page=10, error_out=False)
    this_user = User.query.filter_by(type="admin").first()

    return render_template("search_parking.html", parking_lots=parking_lots.items, this_user=this_user, pagination=parking_lots)


@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    this_user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')

        if fullname:
            this_user.fullname = fullname
        if email:
            this_user.email = email
        if password:
            this_user.pwd = password

        db.session.commit()
        return redirect(f'/profile/{user_id}')

    return render_template('profile.html', this_user=this_user)


# Summary Routes

@app.route("/summary")
def summary():
    this_user = User.query.filter_by(type="admin").first()
    
    available_lots = Info.query.filter_by(status="available").count()
    booked_lots = Info.query.filter_by(status="booked").count()
    
    revenue_by_lot = db.session.query(
        Info.parking,
        db.func.sum(
            db.case(
                (
                    (Info.status == 'booked') & (Info.timestamp != None),
                    (db.func.strftime('%s', 'now') - db.func.strftime('%s', Info.timestamp)) / 3600 * Info.price
                ),
                else_=0
            )
        ).label('revenue')
    ).group_by(Info.parking).all()
    
    return render_template("simple_summary.html",
                         this_user=this_user,
                         available_lots=available_lots,
                         booked_lots=booked_lots,
                         revenue_by_lot=revenue_by_lot)

@app.route("/user_summary/<int:user_id>")
def user_summary(user_id):
    this_user = User.query.get_or_404(user_id)
    
    available_lots = Info.query.filter_by(status="available").count()
    booked_lots = Info.query.filter_by(status="booked", user_id=user_id).count()
    
    revenue_by_lot = db.session.query(
        Info.parking,
        db.func.sum(
            db.case(
                (
                    (Info.status == 'booked') & (Info.timestamp != None),
                    (db.func.strftime('%s', 'now') - db.func.strftime('%s', Info.timestamp)) / 3600 * Info.price
                ),
                else_=0
            )
        ).label('revenue')
    ).filter(Info.user_id == user_id).group_by(Info.parking).all()
    
    return render_template("user_summary.html",
                           this_user=this_user,
                           available_lots=available_lots,
                           booked_lots=booked_lots,
                           revenue_by_lot=revenue_by_lot,
                           user_id=user_id)
