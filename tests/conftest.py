import pytest
from app import create_app, db
from app.models import User, BoltEarnings, UberEarnings, Expense
from datetime import date, timedelta

@pytest.fixture
def app():
    """
    Tworzy aplikację w trybie testowym z in-memory bazą SQLite
    """
    app = create_app(config_name='testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """
    Test client do wykonywania requestów HTTP
    """
    return app.test_client()

@pytest.fixture
def admin_user(app):
    """
    Tworzy użytkownika administratora
    """
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture
def driver_user(app):
    """
    Tworzy użytkownika kierowcy z uber_id i bolt_id
    """
    driver = User(
        username='testdriver',
        role='driver',
        uber_id='test-uber-123',
        bolt_id='test-bolt-456'
    )
    driver.set_password('driver123')
    db.session.add(driver)
    db.session.commit()
    return driver

@pytest.fixture
def bolt_earnings(app, driver_user):
    """
    Tworzy przykładowe zarobki Bolt
    """
    earnings = BoltEarnings(
        user_id=driver_user.id,
        bolt_id=driver_user.bolt_id,
        report_date=date.today(),
        gross_total=1000.00,
        expenses_total=200.00,
        net_income=800.00,
        cash_collected=150.00,
        vat_due=80.00,
        actual_income=720.00
    )
    db.session.add(earnings)
    db.session.commit()
    return earnings

@pytest.fixture
def expense(app, driver_user):
    """
    Tworzy przykładową fakturę kosztową
    """
    exp = Expense(
        user_id=driver_user.id,
        document_number='FV/2025/10/01',
        description='Paliwo',
        issue_date=date.today(),
        net_amount=100.00,
        vat_amount=23.00,
        vat_deductible=11.50,
        deductible_amount=75.00
    )
    db.session.add(exp)
    db.session.commit()
    return exp