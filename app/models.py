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
        return f"<Wydatek {self.document_number} user_id={self.user_id} vatdeductible={self.vat.deductible}>"
    
    @property
    def gross_amount(self):
        """
        Kwota brutto netto + vat
        """
        return self.net_amount + self.vat_amount