from app.models import User, Expense
from datetime import date

def test_user_password_hashing():
    """
    TEST: Sprawdza czy hasła są poprawnie hashowane

    ARANGE: Tworzymy użytkownika
    ACT: Ustawiamy hasło
    ASSERT: Sprawdzamy czy hash działa
    """
    # ARRANGE
    user = User(username='testuser', role='driver')

    # ACT
    user.set_password('mypassword123')

    #ASSERT
    assert user.password_hash is not None #hash został utworzony
    assert user.password_hash != 'mypassword123' # hash =/ plain text
    assert user.check_password('mypassword123') == True #sprawdzanie czy hasło działa
    assert user.check_password('wrongpassword') == False # złe hasło = False

def test_expense_gross_amount_property(app, driver_user):
    """
    TEST: Sprawdza czy property gross_amount działa poprawnie

    fixture 'app' = aplikacja testowa z bazą in-memory
    fixture 'driver_user' = gotowy użytkownik kierowcy
    """
    # ARRANGE
    expense = Expense(
        user_id=driver_user.id,
        document_number='FV/001',
        description='Test',
        issue_date=date.today(),
        net_amount=100.00,
        vat_amount=23.00,
        vat_deductible=11.50,
        deductible_amount=75.00
    )

    # ACT
    gross = expense.gross_amount
    # ASSERT
    assert gross == 123.00 # 100 + 23 = 123