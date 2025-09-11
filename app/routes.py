from flask import render_template, request, flash, redirect, url_for
from flask import current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import AddDriverForm, DriverLoginForm


#trasa logowania, narazie na sztywno
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś poprawnie wylogowany', 'info')
    return redirect(url_for('driver_login'))