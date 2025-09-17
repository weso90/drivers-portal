from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='driver')
    uber_id = db.Column(db.String(128), nullable=True)
    bolt_id = db.Column(db.String(128), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
    

class BoltEarnings(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    #relacja do tabeli User
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref="bolt_earnings")

    #dodatkowe info
    bolt_id = db.Column(db.String(128), nullable=False)

    #dane z CSV (dzienny snapshot)
    report_date = db.Column(db.Date, nullable=False)
    gross_total = db.Column(db.Float, nullable=False) #zarobki ogółem
    expenses_total = db.Column(db.Float, nullable=False) # opłaty ogółem
    net_income = db.Column(db.Float, nullable=False) #Zarobki netto, po odjęciu prowizji
    cash_collected = db.Column(db.Float, nullable=False) # pobrana gótówka
    vat_due = db.Column(db.Float, nullable=False) #należny vat
    actual_income = db.Column(db.Float, nullable=False) #rzeczywisty zarobek

    def __repr__(self):
        return f"<Bolt Earnings {self.report_date} user={self.user_id}"
    
