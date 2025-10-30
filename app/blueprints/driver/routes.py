"""
Blueprint dla panelu kierowcy
"""

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.blueprints.driver import driver_bp

def driver_required(f):
    """
    Dekorator - tylko kierowcy mogą wejść
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'driver':
            flash('Brak uprawnień', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@driver_bp.route('dashboard')
@login_required
@driver_required
def dashboard():
    """
    Panel kierowcy
    URL: /driver/dashboard
    """
    return render_template('driver/dashboard.html', driver=current_user)