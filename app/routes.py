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
    Import danych o zarobkach kierowców z platformy bolt z pliku CSV.
    Obsługuje:
    - wczytanie pliku
    - mapowanie kolumn
    - obliczanie VAT i faktycznego zarobku
    - zapis/aktualizację rekordów w bazie
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
        
        #wczytaj CSV
        try:
            df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, sep=',', engine='python', encoding='utf-8-sig')

        #mapowanie kolumn
        map_cols = {
            "Kierowca": "driver_name",
            "Identyfikator kierowcy": "bolt_id",
            "Zarobki brutto (ogółem)|ZŁ": "gross_total",
            "Opłaty ogółem|ZŁ": "expenses_total",
            "Zarobki netto|ZŁ": "net_income",
            "Pobrana gotówka|ZŁ": "cash_collected",
            "Zarobki brutto (płatności w aplikacji)|ZŁ": "brutto_app",
            "Zarobki brutto (płatności gotówkowe)|ZŁ": "brutto_cash",
            "Zarobki z kampanii|ZŁ": "campaign",
            "Zwroty wydatków|ZŁ": "refunds",
            "Opłaty za anulowanie|ZŁ": "cancellations"
        }

        present = [src for src in map_cols if src in df.columns]
        df = df[present].copy()
        df.rename(columns=map_cols, inplace=True)

        #konsersja na liczby (float)
        for c in ["gross_total", "expenses_total", "net_income", "cash_collected", "brutto_app", "brutto_cash", "campaign", "refunds", "cancellations"]:
            if c in df.columns:
                df[c] = df[c].astype(float)
            else: df[c] = 0.0

        #data raportu z nazwy pliku
        report_date = _extract_date_from_filename(file.filename)
        df["report_date"] = report_date

        #zapis do bazy
        created, updated, skipped = 0, 0, 0
        for _, row in df.iterrows():
            user = None
            if "bolt_id" in row and str(row["bolt_id"]).strip() and str(row["bolt_id"]).lower() != "nan":
                user = User.query.filter_by(bolt_id=str(row["bolt_id"]).strip()).first()
            if user is None and "driver_name" in row and str(row["driver_name"]).strip():
                user = User.query.filter_by(username=str(row["driver_name"]).strip()).first()
            if user is None:
                skipped += 1
                continue

            #Obliczanie vatu
            vat_due = (
                row.get("brutto_app", 0.0) * 0.08 +
                row.get("brutto_cash", 0.0) * 0.08 +
                row.get("campaign", 0.0) * 0.23 +
                row.get("refunds", 0.0) * 0.23 +
                row.get("cancellations", 0.0) * 0.23
            ) - row.get("expenses_total", 0.0) * 0.23

            net_income = float(row.get("net_income", 0.0))
            actual_income = net_income - vat_due
            existing = BoltEarnings.query.filter_by(user_id=user.id, report_date=report_date).first()
            if existing is None:
                rec = BoltEarnings(
                    user_id=user.id,
                    bolt_id=user.bolt_id,
                    report_date=report_date,
                    gross_total=float(row.get("gross_total", 0.0)),
                    expenses_total=float(row.get("expenses_total", 0.0)),
                    net_income=net_income,
                    cash_collected=float(row.get("cash_collected", 0.0)),
                    vat_due = vat_due,
                    actual_income=actual_income
                )
                db.session.add(rec)
                created += 1
            else:
                existing.gross_total = float(row.get("gross_total", 0.0))
                existing.expenses_total = float(row.get("expenses_total", 0.0))
                existing.net_income = net_income
                existing.cash_collected = float(row.get("cash_collected", 0.0))
                existing.vat_due = vat_due
                existing.actual_income = actual_income
                updated += 1

                print("Row:", row.to_dict())
                print("Matched user:", user)
            
        db.session.commit()
        flash(f"Zaimportowano: {created}, zaktualizowano {updated}, pominięto: {skipped}", "success")
        return redirect(url_for('upload_csv'))
    
    return render_template('admin/upload_csv.html', form=form)

@app.route('/admin/upload-uber-csv', methods=['GET', 'POST'])
@login_required
def upload_uber_csv():
    """
    Import danych o zarobkach kierowców z platformy Uber z pliku CSV
    Obsługuje:
    - wczytywanie pliku
    - mapowanie kolumn (z obsługą brakujących kolumn)
    - obliczanie VAT i faktycznego zarobku
    - zapis/aktualizację rekordów w bazie
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
        
        #wczytaj CSV
        try:
            df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, sep=',', engine='python', encoding='utf-8-sig')

        #mapowanie kolumn Uber (wszystkie możliwe kolumny)
        map_cols = {
            "Identyfikator UUID kierowcy": "uber_id",

            "Wypłacono Ci : Twój przychód": "gross_net_income",
            "Wypłacono Ci : Bilans przejazdu : Wypłaty : Odebrana gotówka": "cash_collected",
            "Wypłacono Ci:Twój przychód:Opłata za usługę": "service_fee",
            "Wypłacono Ci:Twój przychód:Opłata:Podatek od opłaty": "tax_on_fee",
            "Wypłacono Ci:Twój przychód:Podatki:Podatek": "tax_general",
            "Wypłacono Ci:Twój przychód:Podatki:Podatek od opłaty za usługę": "tax_on_service_fee",
        }

        #wybierz tylko te kolumny które istnieją w CSV
        present = [src for src in map_cols if src in df.columns]
        df = df[present].copy()
        df.rename(columns=map_cols, inplace=True)

        #konwersja na float, brakujące kolumny = 0.0
        numeric_cols = [
            "gross_net_income", "cash_collected", "service_fee", "tax_on_fee", "tax_general", "tax_on_service_fee"
        ]

        for c in numeric_cols:
            if c in df.columns:
                df[c] = df[c].fillna(0.0).astype(float)
            else:
                df[c] = 0.0

        #data raportu z nazwy pliku
        report_date = _extract_date_from_filename(file.filename)
        df["report_date"] = report_date

        #zapis do bazy
        created, updated, skipped = 0, 0, 0
        for _, row in df.iterrows():
            user = None

            #szukaj użytkownika po uber_id
            if "uber_id" in row and str(row["uber_id"]).strip() and str(row["uber_id"]).lower() != "nan":
                user = User.query.filter_by(uber_id=str(row["uber_id"]).strip()).first()

            #szukaj po imieniu i nazwisku
            if user is None and "first_name" in row and "last_name" in row:
                full_name = f"{row['first_name']} {row['last_name']}".strip()
                user = User.query.filter_by(username=full_name).first()

            if user is None:
                skipped += 1
                continue

            #logika biznesowa uber
            gross_total = float(row.get("gross_net_income", 0.0))
            expenses_total = abs(
                float(row.get("service_fee", 0.0)) +
                float(row.get("tax_on_service_fee", 0.0))
            )

            net_income = float(row.get("gross_net_income", 0.0))
            cash_collected = abs(float(row.get("cash_collected", 0.0)))

            vat_due = (
                float(row.get("tax_on_fee", 0.0)) +
                float(row.get("tax_general", 0.0)) +
                float(row.get("tax_on_service_fee", 0.0))
            )

            actual_income = net_income - vat_due

            existing = UberEarnings.query.filter_by(user_id=user.id, report_date=report_date).first()

            if existing is None:
                rec = UberEarnings(
                    user_id=user.id,
                    uber_id=user.uber_id,
                    report_date=report_date,
                    gross_total=gross_total,
                    expenses_total=expenses_total,
                    net_income=net_income,
                    cash_collected=cash_collected,
                    vat_due=vat_due,
                    actual_income=actual_income
                )
                db.session.add(rec)
                created += 1
            else:
                existing.gross_total = gross_total
                existing.expenses_total = expenses_total
                existing.net_income = net_income
                existing.cash_collected = cash_collected
                existing.vat_due = vat_due
                existing.actual_income = actual_income
                updated += 1
            
        db.session.commit()
        flash(f"zaimportowano Uber: {created} nowych, {updated} zaktualizowanych, {skipped} pominiętych", "success")
        return redirect(url_for('upload_uber_csv'))
    
    return render_template('admin/upload_uber_csv.html', form=form)

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


