from flask import render_template, request, flash, redirect, url_for
from flask import current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, BoltEarnings
from app.forms import AddDriverForm, DriverLoginForm, CSVUploadForm
from datetime import datetime
import pandas as pd
import re

##########################
###   FUNKCJE POMOCNICZE
##########################

def _extract_date_from_filename(filename: str):
    """
    Wyszukuje pierwczą datę w nazwie pliku CSV w formacie DD_MM_RRRR
    Jeśli nie znajdzie to zwraca dzisiejszą datę
    """
    m = re.search(r"\d{2}_\d{2}_\d{4}", filename or "")
    if not m:
        return datetime.utcnow().date()
    return datetime.strptime(m.group(), "%d_%m_%Y").date()


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

        print("=== Import CSV ===")
        print(df.head())

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