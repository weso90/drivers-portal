import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


##########################
###   INICJALIZACJA ROZSZERZEŃ
##########################

#baza danych (SQLAlchemy)
db = SQLAlchemy()

#migracje bazy (Alembic - Flask-Migrate)
migrate = Migrate()

#obsługa logowania (Flask-Login)
login_manager = LoginManager()

#ustawienia dla niezalogowanych
login_manager.login_view = 'login_panel'
login_manager.login_message = 'Strona wymaga logowania'
login_manager.login_message_category = 'warning'

def create_app(config_name='development'):
    """
    Funkcja fabrykująca aplikację Flask.
    Tworzy i konfiguruje instancję aplikacji wraz z rozszerzeniami.

    Args:
        config_name: 'development', 'testing' lub 'production'
    """
    app = Flask(__name__)

    # Wczytaj konfigurację
    if config_name == 'testing':
        from config import TestingConfig
        app.config.from_object(TestingConfig)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    else:
        # Development/Production - wymaga SECRET_KEY z .env
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
        if not app.config['SECRET_KEY']:
            raise ValueError("SECRET_KEY nie został ustawiony! Dodaj go do pliku .env")
        
        basedir = os.path.abspath(os.path.dirname(__file__))
        database_uri = os.environ.get('DATABASE-URI', 'sqlite:///app.db')
        if database_uri.startswith('sqlite:///') and not database_uri.startswith('sqlite:////'):
            db_path = database_uri.replace('sqlite:///', '')
            database_uri = 'sqlite:///' + os.path.join(basedir, db_path)
        
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
        app.config['UPLOAD_FOLDER'] = os.path.join(basedir, '..', os.environ.get('UPLOAD_FOLDER', 'uploads'))
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



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