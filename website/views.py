from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from website import db
from website.models import Tasting
from datetime import datetime

views = Blueprint('views', __name__)

# ----------------------
# List of products
# ----------------------
PRODUCTS = [
    "Pure Blue Vodka",
    "Barrel House Rum",
    "Oak Rum",
    "Devil John Moonshine",
    "Devil John Darkshine",
    "Barrel House Select Bourbon",
    "Barrel House Select Single Barrel Cask",
    "Rockcastle Bourbon",
    "Licking River Rye"
]

# ----------------------
# Dashboard
# ----------------------
@views.route('/dashboard')
@login_required
def dashboard():
    tastings = Tasting.query.filter_by(user_id=current_user.id).all()

    total_tastings = len(tastings)
    total_bottles_sold = 0
    total_tastings_poured = 0

    for t in tastings:
        total_bottles_sold += t.bottles_sold or 0
        total_tastings_poured += t.tastings_poured or 0

    total_conversion = (
        (total_bottles_sold / total_tastings_poured * 100)
        if total_tastings_poured > 0 else 0
    )

    return render_template(
        'dashboard.html',
        total_tastings=total_tastings,
        total_bottles_sold=total_bottles_sold,
        total_tastings_poured=total_tastings_poured,
        total_conversion=total_conversion
    )

# ----------------------
# Submit New Tasting
# ----------------------
@views.route('/submit_tasting', methods=['GET', 'POST'])
@login_required
def submit_tasting():
    if request.method == 'POST':
        date_str = request.form.get('date')
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            date_obj = datetime.now()
        day_of_week = date_obj.strftime("%A")
        store_name = request.form.get('store_name')
        tastings_poured = int(request.form.get('tastings_poured') or 0)

        total_to_sell = total_sold = total_left = 0
        products_data = {}

        for p in PRODUCTS:
            field = p.replace(" ", "_").lower()
            to_sell = int(request.form.get(f"{field}_to_sell") or 0)
            sold = int(request.form.get(f"{field}_sold") or 0)
            left = max(to_sell - sold, 0)
            products_data[p] = {"to_sell": to_sell, "sold": sold, "left": left}
            total_to_sell += to_sell
            total_sold += sold
            total_left += left

        other_name = request.form.get("other_product_name")
        if other_name:
            other_to_sell = int(request.form.get("other_to_sell") or 0)
            other_sold = int(request.form.get("other_sold") or 0)
            other_left = max(other_to_sell - other_sold, 0)
            products_data[other_name] = {"to_sell": other_to_sell, "sold": other_sold, "left": other_left}
            total_to_sell += other_to_sell
            total_sold += other_sold
            total_left += other_left

        conversion = (total_sold / tastings_poured * 100) if tastings_poured > 0 else 0

        new_tasting = Tasting(
            user_id=current_user.id,
            day_of_week=day_of_week,
            date=date_obj.date(),
            time=date_obj.time(),
            store_name=store_name,
            tastings_poured=tastings_poured,
            bottles_to_sell=total_to_sell,
            bottles_sold=total_sold,
            bottles_left=total_left,
            poured_to_sold_percent=conversion,
            products=products_data
        )

        db.session.add(new_tasting)
        db.session.commit()
        flash("Tasting submitted!", "success")
        return redirect(url_for("views.my_tastings"))

    now = datetime.now()
    return render_template("form_page.html", products=PRODUCTS, now=now)

# ----------------------
# My Tastings
# ----------------------
@views.route('/my_tastings')
@login_required
def my_tastings():
    tastings_raw = Tasting.query.filter_by(user_id=current_user.id).order_by(Tasting.date.desc()).all()
    tastings_clean = []
    total_all_to_sell = total_all_sold = total_all_left = total_all_poured = 0

    for t in tastings_raw:
        product_breakdown = {}
        total_to_sell = total_sold = total_left = 0

        for p, info in (t.products or {}).items():
            on_hand = info.get("to_sell", 0)
            sold = info.get("sold", 0)
            left = info.get("left", 0)
            product_breakdown[p] = {"on_hand": on_hand, "sold": sold, "left": left}
            total_to_sell += on_hand
            total_sold += sold
            total_left += left

        poured = t.tastings_poured or 0
        conversion = (total_sold / poured * 100) if poured > 0 else 0

        tastings_clean.append({
            "id": t.id,
            "date": t.date.strftime("%Y-%m-%d"),
            "time": t.time.strftime("%H:%M"),
            "day": t.day_of_week,
            "store": t.store_name,
            "tastings_poured": poured,
            "total_to_sell": total_to_sell,
            "total_sold": total_sold,
            "total_left": total_left,
            "conversion": conversion,
            "products": product_breakdown
        })

        total_all_to_sell += total_to_sell
        total_all_sold += total_sold
        total_all_left += total_left
        total_all_poured += poured

    cumulative_conversion = (total_all_sold / total_all_poured * 100) if total_all_poured > 0 else 0

    return render_template(
        "mytastings.html",
        tastings=tastings_clean,
        total_all_to_sell=total_all_to_sell,
        total_all_sold=total_all_sold,
        total_all_left=total_all_left,
        cumulative_conversion=cumulative_conversion
    )

# ----------------------
# Edit Tasting
# ----------------------
@views.route("/edit_tasting/<int:tasting_id>", methods=["GET", "POST"])
@login_required
def edit_tasting(tasting_id):
    tasting = Tasting.query.get_or_404(tasting_id)
    if tasting.user_id != current_user.id:
        flash("You cannot edit this tasting.", "error")
        return redirect(url_for("views.my_tastings"))

    if request.method == "POST":
        tastings_poured = int(request.form.get("tastings_poured") or 0)
        total_to_sell = total_sold = total_left = 0
        products_data = {}

        for p in PRODUCTS:
            field = p.replace(" ", "_").lower()
            to_sell = int(request.form.get(f"{field}_to_sell") or 0)
            sold = int(request.form.get(f"{field}_sold") or 0)
            left = max(to_sell - sold, 0)

            products_data[p] = {"to_sell": to_sell, "sold": sold, "left": left}

            total_to_sell += to_sell
            total_sold += sold
            total_left += left

        tasting.tastings_poured = tastings_poured
        tasting.bottles_to_sell = total_to_sell
        tasting.bottles_sold = total_sold
        tasting.bottles_left = total_left
        tasting.poured_to_sold_percent = (
            (total_sold / tastings_poured * 100) if tastings_poured else 0
        )
        tasting.products = products_data

        db.session.commit()
        flash("Tasting updated!", "success")
        return redirect(url_for("views.my_tastings"))

    # Prepare values for edit form
    product_values = {}
    for p in PRODUCTS:
        field = p.replace(" ", "_").lower()
        if p in tasting.products:
            product_values[field] = tasting.products[p]
        else:
            product_values[field] = {"to_sell": 0, "sold": 0}

    return render_template(
        "edittastings.html",
        products=PRODUCTS,
        tasting=tasting,
        product_values=product_values
    )

# ----------------------
# Delete Tasting
# ----------------------
@views.route('/delete_tasting/<int:tasting_id>', methods=['POST'])
@login_required
def delete_tasting(tasting_id):
    tasting = Tasting.query.get_or_404(tasting_id)
    if tasting.user_id != current_user.id:
        flash("You cannot delete this tasting.", "error")
        return redirect(url_for('views.my_tastings'))

    db.session.delete(tasting)
    db.session.commit()
    flash("Tasting deleted!", "success")
    return redirect(url_for('views.my_tastings'))
