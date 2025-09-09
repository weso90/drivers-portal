from flask import Flask

def create_app():
    app = Flask(__name__)

    # sekretny klucz do obsługi sesji
    app.config['SECRET_KEY'] = 'sekretny-klucz'
    
    with app.app_context():
        from . import routes

    return app