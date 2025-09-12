from flask import render_template, request, flash, redirect, url_for, jsonify
from flask import current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bolt_api
from app.models import User
from app.forms import AddDriverForm, DriverLoginForm
from datetime import datetime
from collections import defaultdict


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    #jeżeli administrator jest już zalogowany, przenieś go do strony admin_dashboard
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        #sprawdzamy po wprowadzeniu danych do formularza czy użytkownik istnieje, hasło się zgadza i czy ma rolę admin
        if user and user.check_password(password) and user.role == 'admin':
            login_user(user) #funkcja z Flask-Login do zalogowania użytkownika
            flash('Zalogowano pomyślnie', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Nieprawidłowe dane bądź brak uprawnień', 'danger')
            return redirect(url_for('admin_login'))
        
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
@login_required # wymagane zalogowanie do wejścia na stronę
def admin_dashboard():
    #jeżeli nie loguje się administrator to przekierowanie na stronę admin_login
    if current_user.role != 'admin':
        flash('Brak uprawnień administratora', 'danger')
        return redirect(url_for('admin_login'))
    
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/dashboard.html', drivers=drivers)


@app.route('/admin/add_driver', methods=['GET', 'POST'])
@login_required
def add_driver():
    if current_user.role != 'admin':
        flash('Brak uprawnień administratora', 'danger')
        return redirect(url_for('admin_login'))
    
    form = AddDriverForm()
    if form.validate_on_submit():
        new_driver = User(
            username=form.username.data,
            role='driver',
            uber_id=form.uber_id.data,
            bolt_id=form.bolt_id.data
        )
        new_driver.set_password(form.password.data)
        db.session.add(new_driver)
        db.session.commit()
        flash(f'Konto dla kierowcy {new_driver.username} zostało utworzone', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_driver.html', form=form)

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def driver_login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'driver':
            return redirect(url_for('driver_dashboard'))
        
    form = DriverLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('driver_dashboard'))
        else:
            flash('Nieprawidłowe dane logowania', form=form)

    return render_template('driver/login.html', form=form)

@app.route('/dashboard')
@login_required
def driver_dashboard():
    if current_user.role != 'driver':
        flash('Brak uprawnień.', 'danger')
        return redirect(url_for('driver_login'))
    
    return render_template('driver/dashboard.html', driver=current_user)

@app.route('/admin/reports/bolt')
@login_required
def admin_bolt_report():
    if current_user.role != 'admin':
        flash('Brak uprawnień.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str or not end_date_str:
        flash('Proszę wybrać początkową i końcową datę raportu.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if (end_date - start_date).days > 31:
        flash('Zakres dat nie może przekraczać 31 dni.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    orders = bolt_api.get_fleet_orders_for_range(start_date, end_date)

    if orders is None:
        flash('Nie udało się pobrać danych z API Bolt. Sprawdź logi serwera.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    driver_settlements = defaultdict(lambda: {
        'driver_name': "nieznany kierowca", 'total_trips': 0, 'ride_price': 0, 'booking_fee': 0,
        'toll_fee': 0, 'cancellation_fee': 0, 'tip': 0, 'net_earnings': 0,
        'cash_discount': 0, 'in_app_discount': 0, 'commission': 0
    })

    for order in orders:
        price = order.get("order_price", {})
        driver_uuid = order.get("driver_uuid")

        if not driver_uuid or not price:
            continue

        driver_settlements[driver_uuid]['driver_name'] = order.get("driver_name", driver_settlements[driver_uuid]['driver_name'])
        driver_settlements[driver_uuid]['total_trips'] += 1
        
        driver_settlements[driver_uuid]['ride_price'] += price.get('ride_price') or 0
        driver_settlements[driver_uuid]['booking_fee'] += price.get('booking_fee') or 0
        driver_settlements[driver_uuid]['toll_fee'] += price.get('toll_fee') or 0
        driver_settlements[driver_uuid]['cancellation_fee'] += price.get('cancellation_fee') or 0
        driver_settlements[driver_uuid]['tip'] += price.get('tip') or 0
        driver_settlements[driver_uuid]['net_earnings'] += price.get('net_earnings') or 0
        driver_settlements[driver_uuid]['cash_discount'] += price.get('cash_discount') or 0
        driver_settlements[driver_uuid]['in_app_discount'] += price.get('in_app_discount') or 0
        driver_settlements[driver_uuid]['commission'] += price.get('commission') or 0

    sorted_settlements = sorted(driver_settlements.values(), key=lambda x: x['net_earnings'], reverse=True)

    return render_template(
        'admin/bolt_report.html',
        start_date=start_date,
        end_date=end_date,
        settlements=sorted_settlements,
        total_order_count=len(orders)
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś poprawnie wylogowany', 'info')
    return redirect(url_for('driver_login'))