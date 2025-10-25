import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Bazowa konfiguracja
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """
    Konfiguracja development
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'app', 'app.db')
    
class TestingConfig(Config):
    """
    Konfiguracja testowa    
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    UPLOAD_FOLDER = '/tmp/test_uploads'
    MAX_CONTENT_LENGTH = 16777216