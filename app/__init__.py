import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

#przekierowanie niezalogowanych na admin_login
login_manager.login_view = 'admin_login'
#komunikat dla niezalogowanych
login_manager.login_message = 'Strona wymaga logowania'
login_manager.login_message_category = 'warning'

def create_app():
    app = Flask(__name__)

    # sekretny klucz do obsługi sesji
    app.config['SECRET_KEY'] = 'sekretny-klucz'

    #Konfiguracja bazy danych SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    #powiązanie obiektów z aplikacją
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    with app.app_context():
        from . import routes, models

        #potrzebne do stworzenia konta administratora w konsoli
        from . import commands

    return app

#pobieranie użytkownika z bazy na podstawie ID zapisanego w sesji - wymagane przez Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
