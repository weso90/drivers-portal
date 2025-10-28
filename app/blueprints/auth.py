"""
Blueprint dla autoryzacji (logowanie, wylogowanie).
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User
from app.forms import DriverLoginForm

# Blueprint
# 'auth' - nazwa blueprintu (używana w url_for)
# __name__ - nazwa modułu (dla Flask)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Panel logowania dla admina i kierowcy

    Blueprint: auth
    Route: / lub /login
    Pełny URL: */login
    """

    # Jeśli już zalogowany - przekieruj do odpowiedniego panelu
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard')) # <- Blueprint.function
        elif current_user.role == 'driver':
            return redirect(url_for('driver.dashboard')) # <- Blueprint.function
        
    form = DriverLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('driver.dashboard'))
        else:
            flash('Nieprawidłowe dane logowania', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    """
    Wylogowanie użytkownika.

    Blueprint: auth
    Route: /logout
    Pełny URL: */logout
    """
    logout_user()
    flash('Zostałeś poprawnie wylogowany', 'info')
    return redirect(url_for('auth.login')) # <- Przekierowanie do auth.login