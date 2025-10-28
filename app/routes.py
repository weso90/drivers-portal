from flask import render_template, request, flash, redirect, url_for
from flask import current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, BoltEarnings, UberEarnings, Expense
from app.forms import AddDriverForm, DriverLoginForm, CSVUploadForm, AddExpenseForm
from datetime import datetime
import pandas as pd
import re

##########################
###   FUNKCJE POMOCNICZE
##########################

def _extract_date_from_filename(filename: str):
    """
    Wyszukuje datę w nazwie pliku CSV.
    Formaty:
    Bolt: DD_MM_RRRR
    Uber: YYYYMMDD
    Jeśli nie znajdzie to zwraca dzisiejszą datę
    """
    m = re.search(r"(\d{8})", filename or "")
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            pass
    
    m = re.search(r"(\d{2}_\d{2}_\d{4})", filename or "")
    if m:
        try:
            return datetime.strptime(m.group(1), "%d_%m_%Y").date()
        except ValueError:
            pass
    return datetime.utcnow().date()


##########################
###   ADMIN ROUTES
##########################

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """
    Panel administratora
    """
    #jeżeli nie loguje się administrator to przekierowanie na stronę admin_login
    if current_user.role != 'admin':
        flash('Brak uprawnień administratora', 'danger')
        return redirect(url_for('login_panel'))
    
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/dashboard.html', drivers=drivers)



@app.route('/admin/add_driver', methods=['GET', 'POST'])
@login_required
def add_driver():
    """
    Formularz dodawania nowego kierowcy przez administratora
    """
    if current_user.role != 'admin':
        flash('Brak uprawnień administratora', 'danger')
        return redirect(url_for('login_panel'))
    
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

@app.route('/admin/driver/<int:driver_id>/earnings', methods=['GET'])
@login_required
def driver_earnings(driver_id):
    """
    Wyświetla zarobki konkretnego kierowcy z możliwością filtrowania po dacie.
    """
    if current_user.role != 'admin':
        flash('Brak uprawnień administratora', 'danger')
        return redirect(url_for('login_panel'))
    
    driver = User.query.get_or_404(driver_id)
    if driver.role != 'driver':
        flash('Ten użytkownik nie jest kierowcą', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    #pobierz parametry z query string (filtrowanie po dacie)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    # query dla bolt
    bolt_query = BoltEarnings.query.filter_by(user_id=driver_id)
    if date_from:
        bolt_query = bolt_query.filter(BoltEarnings.report_date >= date_from)
    if date_to:
        bolt_query = bolt_query.filter(BoltEarnings.report_date <= date_to)
    bolt_earnings = bolt_query.order_by(BoltEarnings.report_date.desc()).all()

    #query dla uber
    uber_query = UberEarnings.query.filter_by(user_id=driver_id)
    if date_from:
        uber_query = uber_query.filter(UberEarnings.report_date >= date_from)
    if date_to:
        uber_query = uber_query.filter(UberEarnings.report_date <= date_to)
    uber_earnings = uber_query.order_by(UberEarnings.report_date.desc()).all()

    # Query dla faktur kosztowych
    expenses_query = Expense.query.filter_by(user_id=driver_id)
    if date_from:
        expenses_query = expenses_query.filter(Expense.issue_date >= date_from)
    if date_to:
        expenses_query = expenses_query.filter(Expense.issue_date <= date_to)
    expenses = expenses_query.order_by(Expense.issue_date.desc()).all()

    #oblicz sumy
    bolt_total = {
        'gross': sum(float(e.gross_total) for e in bolt_earnings),
        'cash': sum(float(e.cash_collected) for e in bolt_earnings),
        'vat': sum(float(e.vat_due) for e in bolt_earnings),
        'actual': sum(float(e.actual_income) for e in bolt_earnings),
    }
    
    uber_total = {
        'gross': sum(float(e.gross_total) for e in uber_earnings),
        'cash': sum(float(e.cash_collected) for e in uber_earnings),
        'vat': sum(float(e.vat_due) for e in uber_earnings),
        'actual': sum(float(e.actual_income) for e in uber_earnings),
    }

    # Suma faktur kosztowych
    expenses_total = {
        'net': sum(float(e.net_amount) for e in expenses),
        'vat': sum(float(e.vat_amount) for e in expenses),
        'vat_deductible': sum(float(e.vat_deductible) for e in expenses),
        'deductible': sum(float(e.deductible_amount) for e in expenses),
    }

    return render_template(
        'admin/driver_earnings.html',
        driver=driver,
        bolt_earnings=bolt_earnings,
        uber_earnings=uber_earnings,
        bolt_total=bolt_total,
        uber_total=uber_total,
        expenses=expenses,
        expenses_total=expenses_total,
        date_from=date_from,
        date_to=date_to
    )

@app.route('/admin/upload-csv', methods=['GET', 'POST'])
@login_required
def upload_csv():
    """
    Uniwersalny import CSV - automatycznie rozpoznaje platformę (Bolt/Uber).
    """
    if current_user.role != 'admin':
        flash('Brak uprawnień administratora', 'danger')
        return redirect(url_for('login_panel'))
    form = CSVUploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        file = form.file.data
        if not file:
            flash('Nie wybrano pliku', 'warning')
            return redirect(request.url)
        
        try:
            # Automatyczne rozpoznanie i przetwarzania
            from app.csv_processor import CSVProcessor
            processor = CSVProcessor(file, file.filename)
            result = processor.process()

            platform_name = 'Bolt' if result['platform'] == 'bolt' else 'Uber'
            flash(
                f"Zaimportowano {platform_name}: {result['created']} nowych, "
                f"{result['updated']} zaktualizowanych, {result['skipped']} pominiętych",
                "success"
            )
        except ValueError as e:
            flash(f'Błąd: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Błąd podczas importu: {str(e)}', 'danger')

        return redirect(url_for('upload_csv'))
    return render_template('admin/upload_csv.html', form=form)

@app.route('/admin/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    """
    Formularz dodawania faktury kosztowej przez administratora.
    Oblicza automatycznie:
    -vat_deductible = vat_amount / 2
    -deductible_amount = net_amount * 0.75
    """
    if current_user.role != 'admin':
        flash('Brak uprawnień administratora', 'danger')
        return redirect(url_for('login_panel'))
    
    form = AddExpenseForm()

    #wypełnij listę kierowców w SelectField
    drivers = User.query.filter_by(role='driver').all()
    form.driver_id.choices = [(d.id, d.username) for d in drivers]

    if form.validate_on_submit():
        #oblicz automatyczne wartości
        vat_deductible = float(form.vat_amount.data) / 2
        deductible_amount = float(form.net_amount.data) * 0.75

        #obsługa uploadu zdjęcia
        filename = None
        if form.image.data:
            from werkzeug.utils import secure_filename
            import os

            file = form.image.data
            filename = secure_filename(file.filename)

            #dodaj timestamp do nazwy pliku (unikalne nazwy)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"

            #zapisz plik
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

        #stwórz rekord faktury
        expense = Expense(
            user_id=form.driver_id.data,
            document_number=form.document_number.data,
            description=form.description.data,
            issue_date=form.issue_date.data,
            net_amount=form.net_amount.data,
            vat_amount=form.vat_amount.data,
            vat_deductible=vat_deductible,
            deductible_amount=deductible_amount,
            image_filename=filename
        )

        db.session.add(expense)
        db.session.commit()

        flash(f'Faktura {expense.document_number} została dodana', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_expense.html', form=form)



##########################
###   DRIVER ROUTES
##########################

@app.route('/dashboard')
@login_required
def driver_dashboard():
    """
    Prosty panel kierowcy - do rozbudowy
    """
    if current_user.role != 'driver':
        flash('Brak uprawnień.', 'danger')
        return redirect(url_for('login_panel'))
    
    return render_template('driver/dashboard.html', driver=current_user)



##########################
###   LOGOWANIE I WYLOGOWYWANIE
##########################

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login_panel():
    """
    Panel logowania
    """
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
            flash('Nieprawidłowe dane logowania', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """
    Wylogowywanie użytkownika - admina lub kierowcy
    użyte Flask-Login
    """
    logout_user()
    flash('Zostałeś poprawnie wylogowany', 'info')
    return redirect(url_for('login_panel'))


