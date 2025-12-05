from flask import Blueprint, render_template, redirect, request, url_for, flash
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

# -------------------
# Login (Home Page)
# -------------------
@auth.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('views.dashboard'))  # dashboard after login
        else:
            flash("Incorrect email or password.", "error")

    return render_template("login.html")


# -------------------
# Signup
# -------------------
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        special_code = request.form.get('special_code')

        # Check special signup code
        if special_code != "1234":
            flash("Invalid special code.", "error")
            return redirect(url_for('auth.signup'))

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for('auth.signup'))

        # Hash password and create user
        hashed_password = generate_password_hash(password)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template("signup.html")


# -------------------
# Logout
# -------------------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
