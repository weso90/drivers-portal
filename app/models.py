from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
from datetime import datetime

##########################
###   MODEL UŻYTKOWNIKA
##########################

class User(UserMixin, db.Model):
    """
    Model użytkownika systemu (admin lub kierowca).
    Pola:
    - username: login do systemu
    - password_hash: hasło (hashowane)
    - role: rola użytkownika (admin lub driver)
    - uber_id: identyfikator kierowcy Uber
    - bolt_id: identyfikator kierowcy Bolt
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='driver')
    uber_id = db.Column(db.String(128), nullable=True)
    bolt_id = db.Column(db.String(128), nullable=True)

    #relacja: jeden użytkownik może mieć wiele wpisów w tabeli BoltEarnings
    bolt_earnings = db.relationship("BoltEarnings", backref="user", lazy=True)
    uber_earnings = db.relationship("UberEarnings", backref="user", lazy=True)
    expenses = db.relationship("Expense", backref="user", lazy=True)

    #metody do obsługi haseł
    def set_password(self, password):
        """
        Ustawia hash hasła dla użytkownika.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Sprawdza poprawność podanego hasła.
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'



##########################
###   MODEL ZAROBKÓW BOLT
##########################

class BoltEarnings(db.Model):
    """
    Model przechowujący dane o zarobkach z platformy Bolt
    Pola:
    - user_id: powiązanie z użytkownikiem (User)
    - bolt_id: identyfikator kierowcy Bolt
    - report_date: data raportu (pochodząca z nazwy pliku CSV)
    - gross_total: zarobki brutto (ogółem)
    - expenses_total: opłaty ogółem
    - net_income: zarobki netto
    - cash_collected: pobrana gotówka
    - vat_due: należny vat (wyliczany według wzoru)
    - actual_income: faktyczny zarobek - net_income - vat_due
    """
    id = db.Column(db.Integer, primary_key=True)

    #relacja z tabelą User
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    bolt_id = db.Column(db.String(128), nullable=False)

    #dane z CSV (dzienny snapshot)
    report_date = db.Column(db.Date, nullable=False)
    gross_total = db.Column(db.Numeric(10, 2), nullable=False, default=0) #zarobki ogółem
    expenses_total = db.Column(db.Numeric(10, 2), nullable=False, default=0) # opłaty ogółem
    net_income = db.Column(db.Numeric(10, 2), nullable=False, default=0) #Zarobki netto, po odjęciu prowizji
    cash_collected = db.Column(db.Numeric(10, 2), nullable=False, default=0) # pobrana gótówka

    #wartości liczone z danych z pliku csv
    vat_due = db.Column(db.Numeric(10, 2), nullable=False, default=0) #należny vat
    actual_income = db.Column(db.Numeric(10, 2), nullable=False, default=0) #rzeczywisty zarobek

    def __repr__(self):
        return f"<Bolt Earnings {self.user_id} {self.report_date}>"
    

##########################
###   MODEL ZAROBKÓW UBER
##########################

class UberEarnings(db.Model):
    """
    Model przechowujący dane o zarobkach z platformy Uber
    Pola:
    - user_id: powiązanie z użytkownikiem (User)
    - uber_id: identyfikator kierowcy Bolt
    - report_date: data raportu (pochodząca z nazwy pliku CSV)
    - gross_total: zarobki brutto (ogółem)
    - expenses_total: opłaty ogółem
    - net_income: zarobki netto
    - cash_collected: pobrana gotówka
    - vat_due: należny vat (wyliczany według wzoru)
    - actual_income: faktyczny zarobek - net_income - vat_due
    """
    id = db.Column(db.Integer, primary_key=True)

    #relacja z tabelą User
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uber_id = db.Column(db.String(128), nullable=False)

    #dane z CSV (dzienny snapshot)
    report_date = db.Column(db.Date, nullable=False)
    gross_total = db.Column(db.Numeric(10, 2), nullable=False, default=0) #zarobki ogółem
    expenses_total = db.Column(db.Numeric(10, 2), nullable=False, default=0) # opłaty ogółem
    net_income = db.Column(db.Numeric(10, 2), nullable=False, default=0) #Zarobki netto, po odjęciu prowizji
    cash_collected = db.Column(db.Numeric(10, 2), nullable=False, default=0) # pobrana gótówka

    #wartości liczone z danych z pliku csv
    vat_due = db.Column(db.Numeric(10, 2), nullable=False, default=0) #należny vat
    actual_income = db.Column(db.Numeric(10, 2), nullable=False, default=0) #rzeczywisty zarobek

    def __repr__(self):
        return f"<Uber Earnings {self.user_id} {self.report_date}>"
    
##########################
###   MODEL FAKTUR KOSZTOWYCH
##########################

class Expense(db.Model):
    """
    Model przechowujący faktury kosztowe kierowców (do odliczenia VAT)
    Pola:
    - user_id: powiązanie z użytkownikiem (kierowcą)
    - document_number: numer faktury/dokumentu
    - description: za co jest faktura (np. "paliwo", "myjnia")
    - issue_date: data wystawienia faktury
    - net_amount: kwota netto z faktury (wpisywana ręcznie)
    - vat_amount: kwota VAT z faktury (wpisywana ręcznie)
    - vat_deductible: VAT do odliczenia = vat_amount / 2 (obliczane automatycznie)
    - deductible_amount: kwota do odliczenia = 75% netto (obliczane automatycznie)
    - image_filename: nazwa pliku ze zdjęciem faktury
    - created_at: kiedy dodano do systemu (automatycznie)
    """

    id = db.Column(db.Integer, primary_key=True)

    #relacja z użytkownikiem (kierowcą)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    #dane faktury
    document_number = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)

    #kwoty
    net_amount = db.Column(db.Numeric(10, 2), nullable=False) # netto z faktury
    vat_amount = db.Column(db.Numeric(10, 2), nullable=False) # vat z faktury
    vat_deductible = db.Column(db.Numeric(10, 2), nullable=False) # vat do odliczenia
    deductible_amount = db.Column(db.Numeric(10, 2), nullable=False) # 75% netto do odliczenia

    #zdjęcie faktury
    image_filename = db.Column(db.String(256), nullable=True)

    #metadata
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Wydatek {self.document_number} user_id={self.user_id} vat_deductible={self.vat_deductible}>"
    
    @property
    def gross_amount(self):
        """
        Kwota brutto netto + vat
        """
        return self.net_amount + self.vat_amount
    

##########################
###   MODEL RAPORTÓW TYGODNIOWYCH
##########################

class WeeklyReport(db.Model):
    """
    Model przechowujący wygenerowane raporty tygodniowe dla kierowców

    Pola:
    - user_id: powiązanie z kierowcą
    - report_name: nazwa raportu (np Tydzień 40/2024)
    - date_from: data początkowa raportu
    - date_to: data końcowa raportu
    - generated_at: kiedy wygenerowano raport

    Zarobki (z Bolt + Uber):
    - total_gross: suma zarobków
    - total_cash: suma odebranej gotówki
    - total_vat_calculated: wyliczony VAT (może być ujemny)
    - total_vat: VAT do zapłaty w tym raporcie (>= 0)
    - vat_carryover: VAT do przeniesienia na następny raport
    - total_actual: faktyczny zarobek po VAT

    Faktury kosztowe:
    - expenses_net: suma netto z faktur
    - expenses_vat: suma VAT z faktur
    - expenses_vat_deductible: VAT do odliczenia (50%)
    - expenses_deductible: kwota do odliczenia (75% netto)

    Odliczenia:
    - settlement_fee: opłata za rozliczenie (30zł checkbox)
    - contract_fee: umowa zlecenie (150zł checkbox)
    - fuel_amount: kwota za paliwo (wpisywana ręcznie)

    Podsumowanie:
    - final_amount: końcowa kwota do wypłaty
    """

    id = db.Column(db.Integer, primary_key=True)

    #relacja z użytkownikiem
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    #metadane raportu
    report_name = db.Column(db.String(128), nullable=False)
    date_from = db.Column(db.Date, nullable=False)
    date_to = db.Column(db.Date, nullable=False)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    #zarobki (Bolt+Uber)
    total_gross = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_cash = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    #VAT
    total_vat_calculated = db.Column(db.Numeric(10, 2), nullable=False, default=0) #wyliczony, może być ujemny
    total_vat = db.Column(db.Numeric(10, 2), nullable=False, default=0) #do zapłaty (>=0)
    vat_carryover = db.Column(db.Numeric(10, 2), nullable=False, default=0) #do przeniesienia, może być ujemny

    total_actual = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    #faktury kosztowe
    expenses_net = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    expenses_vat = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    expenses_vat_deductible = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    expenses_deductible = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    #odliczenia
    settlement_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    contract_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    fuel_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # końcowa kwota
    final_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    def __repr__(self):
        return f"<WeeklyReport {self.report_name} user_id{self.user_id} final={self.final_amount}>"
    
    @property
    def total_deductions(self):
        """
        Suma wszystkich odliczeń
        """
        return self.settlement_fee + self.contract_fee + self.fuel_amount
    
    @property
    def earnings_without_cash(self):
        """
        Zarobek bez gotówki (przed odliczeniami)
        """
        return self.total_actual - self.total_cash
    
    @classmethod
    def get_last_vat_carryover(cls, user_id):
        """
        Pobiera VAT do przeniesienia z ostatniego raportu kierowcy

        Returns:
            Decimal: kwota VAT do przeniesienia (ujemna lub 0)
        """
        last_report = cls.query.filter_by(user_id=user_id).order_by(cls.date_to.desc()).first()

        if last_report and last_report.vat_carryover < 0:
            return float(last_report.vat_carryover)
        return 0.0