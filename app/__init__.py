import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()

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
    
    with app.app_context():
        from . import routes, models

    return app