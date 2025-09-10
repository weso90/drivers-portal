from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    role = db.Column(db.String(20), nullable=False, default='driver')
    uber_id = db.Column(db.String(128), nullable=True)
    bolt_id = db.Column(db.String(128), nullable=True)

    def set_password(self, password):
        """Tworzy hash hasła."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Sprawdza hash hasła."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'