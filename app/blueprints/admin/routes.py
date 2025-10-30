"""
Blueprint dla panelu administratora.
Obsługuje zarządzanie kierowcami, import CSV, faktury kosztowe.
"""

from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.blueprints.admin import admin_bp
from app import db
from app.models import User, BoltEarnings, UberEarnings, Expense
from app.forms import AddDriverForm, CSVUploadForm, AddExpenseForm
import os
from werkzeug.utils import secure_filename




def admin_required(f):
    """
    Dekorator sprawdzający czy użytkownik ma rolę 'admin'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Brak uprawnień administratora', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function



@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """
    Panel administratora
    """
    
    drivers = User.query.filter_by(role='driver').all()
    return render_template('admin/dashboard.html', drivers=drivers)



@admin_bp.route('/add_driver', methods=['GET', 'POST'])
@login_required
@admin_required
def add_driver():
    """
    Formularz dodawania nowego kierowcy przez administratora
    """    
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
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/add_driver.html', form=form)

@admin_bp.route('/driver/<int:driver_id>/earnings', methods=['GET'])
@login_required
@admin_required
def driver_earnings(driver_id):
    """
    Wyświetla zarobki konkretnego kierowcy z możliwością filtrowania po dacie.
    """
    driver = User.query.get_or_404(driver_id)
    if driver.role != 'driver':
        flash('Ten użytkownik nie jest kierowcą', 'warning')
        return redirect(url_for('admin.dashboard'))

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

@admin_bp.route('/upload-csv', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_csv():
    """
    Uniwersalny import CSV - automatycznie rozpoznaje platformę (Bolt/Uber).
    """
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

        return redirect(url_for('admin.upload_csv'))
    return render_template('admin/upload_csv.html', form=form)

@admin_bp.route('/add-expense', methods=['GET', 'POST'])
@login_required
@admin_required
def add_expense():
    """
    Formularz dodawania faktury kosztowej przez administratora.
    Oblicza automatycznie:
    -vat_deductible = vat_amount / 2
    -deductible_amount = net_amount * 0.75
    """    
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
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
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
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/add_expense.html', form=form)