from flask import render_template, request, flash, redirect, url_for, session
from flask import current_app as app
from app import db
from app.models import User
from app.forms import AddDriverForm


#trasa logowania, narazie na sztywno
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'password':
            session['admin_logged_in'] = True
            flash('zalogowano pomyślnie', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('nieprawidłowe dane logowania', 'danger')
            return redirect(url_for('admin_login'))
        
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Strona wymaga logowania', 'warning')
        return redirect(url_for('admin_login'))
    
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/dashboard.html', drivers=drivers)

@app.route('/admin/add_driver', methods=['GET', 'POST'])
def add_driver():
    if not session.get('admin_logged_in'):
        flash('Brak uprawnień', 'danger')
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

#wylogowywanie
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('admin_login'))