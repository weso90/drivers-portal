from flask import render_template, request, flash, redirect, url_for, session
from flask import current_app as app


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
        
#prosty panel admina
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Strona wymaga logowania', 'warning')
        return redirect(url_for('admin_login'))
    
    return "<h1>Witaj w panelu administratora!</h1><a href='/admin/logout'>Wyloguj</a>"


#wylogowywanie
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('admin_login'))