import pytest
from app import create_app, db
from app.models import User, BoltEarnings, UberEarnings, Expense
from datetime import date

@pytest.fixture(scope='function')
def app():
    """Tworzy aplikację testową"""
    _app = create_app(config_name='testing')
    
    with _app.app_context():
        db.create_all()
        
    yield _app
    
    with _app.app_context():
        db.drop_all()
        db.session.remove()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    """Admin w bazie"""
    with app.app_context():
        user = User(username='admin', role='admin')
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    with app.app_context():
        yield User.query.get(user_id)

@pytest.fixture
def driver_user(app):
    """Kierowca w bazie"""
    with app.app_context():
        user = User(
            username='testdriver',
            role='driver',
            uber_id='test-uber-123',
            bolt_id='test-bolt-456'
        )
        user.set_password('driver123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    with app.app_context():
        yield User.query.get(user_id)

@pytest.fixture
def bolt_earnings(app, driver_user):
    """Zarobki Bolt w bazie"""
    with app.app_context():
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
        earnings_id = earnings.id
    
    with app.app_context():
        yield BoltEarnings.query.get(earnings_id)

@pytest.fixture
def expense(app, driver_user):
    """Expense w bazie"""
    with app.app_context():
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
        exp_id = exp.id
    
    with app.app_context():
        yield Expense.query.get(exp_id)