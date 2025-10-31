"""
Testy blueprintu Admin (panel administratora)
"""
import pytest
from app.models import User, BoltEarnings, UberEarnings, Expense

class TestAdminDashboard:
    """
    testy dashboardu administratora
    """

    def test_admin_requires_login(self, client):
        """
        TEST: Niezalogowany user próbuje wejść na /admin/dashboard -> redirect na /login
        """
        response = client.get('/admin/dashboard')

        assert response.status_code == 302
        assert '/login' in response.location

    def test_driver_cannot_access_admin_dashboard(self, client, driver_user):
        """
        TEST: Kierowca próbuje wejść na admin dashboard -> brak uprawnień
        """
        #zaloguj się jako kierowca
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        #spróbuj wejść na admin panel
        response = client.get('/admin/dashboard', follow_redirects=True)

        assert response.status_code == 200
        assert 'Brak uprawnień administratora' in response.data.decode('utf-8')

    def test_admin_can_access_dashboard(self, client, admin_user):
        """
        TEST: Admin wchodzi na swój dashboard -> sukces
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #wejdź na dashboard
        response = client.get('/admin/dashboard')

        assert response.status_code == 200
        assert 'Panel Administratora' in response.data.decode('utf-8')
        assert 'Zarządzaj kierowcami' in response.data.decode('utf-8')

    def test_admin_dashboard_shows_empty_drivers_list(self, client, admin_user):
        """
        TEST: Admin dashboard bez kierowców -> komunikat "Brak dodanych kierowców"
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/dashboard')

        assert response.status_code == 200
        assert 'Brak dodanych kierowców' in response.data.decode('utf-8')

    def test_admin_dashboard_shows_drivers_list(self, client, admin_user, driver_user):
        """
        TEST: Admin dashboard z kierowcami -> wyświetla listę
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('admin/dashboard')
        assert response.status_code == 200
        assert 'testdriver' in response.data.decode('utf-8')
        assert driver_user.uber_id in response.data.decode('utf-8')
        assert driver_user.bolt_id in response.data.decode('utf-8')

    def test_admin_dashboard_has_action_buttons(self, client, admin_user):
        """
        TEST: Admin dashboard ma wszystkie przyciski akcji
        """
        # zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/dashboard')

        assert response.status_code == 200
        assert 'Dodaj nowego kierowcę' in response.data.decode('utf-8')
        assert 'Import zarobków' in response.data.decode('utf-8')
        assert 'Dodaj fakturę' in response.data.decode('utf-8')
        assert '/admin/add_driver' in response.data.decode('utf-8')
        assert '/admin/upload-csv' in response.data.decode('utf-8')
        assert '/admin/add-expense' in response.data.decode('utf-8')

class TestAddDriver:
    """
    Testy dodawania kierowcy przez admina
    """

    def test_add_driver_page_requires_admin(self, client, driver_user):
        """
        TEST: Kierowca nie może wejść na stronę dodawania kierowcy
        """
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        response = client.get('/admin/add_driver', follow_redirects=True)

        assert response.status_code == 200
        assert 'Brak uprawnień administratora' in response.data.decode('utf-8')

    def test_add_driver_page_loads(self, client, admin_user):
        """
        TEST: Admin wchodzi na stronę dodawania kierowcy -> formularz się wyświetla
        """
        # zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/add_driver')

        assert response.status_code == 200
        assert 'Dodaj nowego kierowcę' in response.data.decode('utf-8')
        assert 'Nazwa użytkownika' in response.data.decode('utf-8')
        assert 'Hasło' in response.data.decode('utf-8')
        assert 'Uber driver ID' in response.data.decode('utf-8')
        assert 'Bolt driver ID' in response.data.decode('utf-8')

    def test_add_driver_success(self, client, admin_user, app):
        """
        TEST: Admin pomyślnie dodaje nowego kierowcę
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #dodaj nowego kierowcę
        response = client.post('/admin/add_driver', data={
            'username': 'newdriver',
            'password': 'password123',
            'uber_id': 'uber-new-1',
            'bolt_id': 'bolt-new-1'
        }, follow_redirects=True)

        assert response.status_code == 200
        #sprawdź flash message
        assert 'Konto dla kierowcy newdriver zostało utworzone' in response.data.decode('utf-8')

        #sprawdź czy kierowca jest w bazie
        with app.app_context():
            new_user = User.query.filter_by(username='newdriver').first()
            assert new_user is not None
            assert new_user.role == 'driver'
            assert new_user.uber_id == 'uber-new-1'
            assert new_user.bolt_id == 'bolt-new-1'

    def test_add_driver_duplicate_username(self, client, admin_user, driver_user):
        """
        TEST: Admin próbuje dodać kierowcę z istniejącą nazwą użytkownika -> błąd
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #spróbuj dodać kierowcę z istniejącą nazwą
        response = client.post('/admin/add_driver', data={
            'username': 'testdriver', #już istnieje
            'password': 'password123',
            'uber_id': 'uber-duplicate',
            'bolt_id': 'bolt-duplicate'
        }, follow_redirects=True)

        assert response.status_code == 200
        #sprawdź komunikat błędu
        assert 'Użytkownik o tej nazwie już istnieje' in response.data.decode('utf-8')

    def test_add_driver_missing_required_fields(self, client, admin_user):
        """
        TEST: Admin próbuje dodać kierowcę bez wymaganych pól -> walidacja
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #spróbuj dodać bez username
        response = client.post('/admin/add_driver', data={
            'username': '',
            'password': 'password123',
            'uber_id': 'uber-01',
            'bolt_id': 'bolt-01'
        }, follow_redirects=True)

        assert response.status_code == 200
        #formularz powinien być z powerotem wyświetlony (błąd walidacji)
        assert 'Dodaj nowego kierowcę' in response.data.decode('utf-8')

    def test_added_driver_appears_on_dashboard(self, client, admin_user):
        """
        TEST: nowo dodany kierowca pojawia się na liście w dashboardzie
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #dodaj kierowcę
        client.post('/admin/add_driver', data={
            'username': 'dashboardtest',
            'password': 'password123',
            'uber_id': 'uber-dash-1',
            'bolt_id': 'bolt-dash-1'
        })

        #wejdź na dashboard
        response = client.get('/admin/dashboard')
        
        assert response.status_code == 200
        assert 'dashboardtest' in response.data.decode('utf-8')
        assert 'uber-dash-1' in response.data.decode('utf-8')
        assert 'bolt-dash-1' in response.data.decode('utf-8')

class TestDriverEarnings:
    """
    Testy wyświetlania zarobków kierowcy
    """

    def test_driver_earnings_requires_admin(self, client, driver_user):
        """
        TEST: kierowca nie może wejść na stronę zarobków innego kierowcy
        """
        #zaloguj się jako kierowca
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        #spróbuj wejść na earnings(ID=1 to testdriver, ale sprawdzamy pozwolenia)
        response = client.get('/admin/driver/1/earnings', follow_redirects=True)

        assert response.status_code == 200
        assert 'Brak uprawnień administratora' in response.data.decode('utf-8')

    def test_driver_earnings_page_loads(self, client, admin_user, driver_user):
        """
        TEST: Admin wchodzi na stronę zarobków kierowcy -> formularz filtrowania się wyświetla
        """
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #wejdź na earnings kierowcy
        response = client.get(f'/admin/driver/{driver_user.id}/earnings')

        assert response.status_code == 200
        assert 'Zarobki kierowcy' in response.data.decode('utf-8')
        assert 'testdriver' in response.data.decode('utf-8')
        assert 'Filtruj po dacie' in response.data.decode('utf-8')

    def test_driver_earnings_shows_no_data_message(self, client, admin_user, driver_user):
        """
        TEST: Kierowca bez zarobków -> komunikat "Brak danych"
        """
        #zalogu się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get(f'/admin/driver/{driver_user.id}/earnings')

        assert response.status_code == 200
        assert 'Brak danych' in response.data.decode('utf-8')

    def test_driver_earnings_shows_bolt_earnings(self, client, admin_user, driver_user, bolt_earnings):
        """
        TEST: Kierowca z zarobkami Bolt wyświetla dane Bolt
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get(f'/admin/driver/{driver_user.id}/earnings')

        assert response.status_code == 200
        #sprawdź czy są dane Bolt
        assert 'Bolt' in response.data.decode('utf-8')
        #sprawdź czy są konkretne kwoty z fixture
        assert str(bolt_earnings.gross_total) in response.data.decode('utf-8')

    def test_driver_earnings_nonexistent_driver(self, client, admin_user):
        """
        TEST: Admin próbuje wejść na earnings nieistniejącego kierowcy -> 404
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #spróbuj wejść na nieistniejący ID
        response = client.get('/admin/driver/9999/earnings')

        assert response.status_code == 404

    def test_driver_earnings_back_button(self, client, admin_user, driver_user):
        """
        TEST: Przycisk "Powrót do panelu" działa
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get(f'/admin/driver/{driver_user.id}/earnings')

        assert response.status_code == 200
        assert 'Powrót do panelu' in response.data.decode('utf-8')
        assert '/admin/dashboard' in response.data.decode('utf-8')

class TestUploadCSV:
    """
    Testy uploadu CSV z zarobkami
    """
    def test_upload_csv_requires_admin(self, client, driver_user):
        """
        TEST: Kierowca nie może uploadować CSV
        """
        #zaloguj się jako kierowca
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        response = client.get('/admin/upload-csv', follow_redirects=True)

        assert response.status_code == 200
        assert 'Brak uprawnień administratora' in response.data.decode('utf-8')

    def test_upload_csv_page_loads(self, client, admin_user):
        """
        TEST: admin wchodzi na stronę uploadu CSV -> Formularz się wyświetla
        """
        # Zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/upload-csv')

        assert response.status_code == 200
        assert 'Import zarobków' in response.data.decode('utf-8')
        assert 'Plik CSV' in response.data.decode('utf-8')

    def test_upload_csv_without_file(self, client, admin_user):
        """
        TEST: Admin próbuje uploadować bez wybrania pliku -> błąd walidacji
        """
        # Zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        # POST bez pliku
        response = client.post('/admin/upload-csv', data={}, follow_redirects=True)

        assert response.status_code == 200
        assert 'Import zarobków' in response.data.decode('utf-8')

class TestAddExpense:
    """
    Testy dodawania faktur kosztowych
    """

    def test_add_expense_requires_admin(self, client, driver_user):
        """
        TEST: Kierowca nie może dodawać faktur kosztowych
        """
        # zaloguj się jako kierowca
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        response = client.get('/admin/add-expense', follow_redirects=True)

        assert response.status_code == 200
        assert 'Brak uprawnień administratora' in response.data.decode('utf-8')

    def test_add_expense_page_loads(self, client, admin_user):
        """
        TEST: Admin wchodzi na stronę dodawania faktury -> formularz się wyświetla
        """
        # zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/add-expense')

        assert response.status_code == 200
        assert 'Dodaj fakturę kosztową' in response.data.decode('utf-8')
        assert 'Kwota netto' in response.data.decode('utf-8')
        assert 'VAT' in response.data.decode('utf-8')

    def test_add_expense_success(self, client, admin_user, driver_user, app):
        """
        TEST: Admin może wysłać formularz dodawania faktury
        """
        from datetime import date
        
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.post('/admin/add-expense', data={
            'user_id': driver_user.id,
            'expense_name': 'Paliwo',
            'net_amount': '500.00',
            'vat_amount': '115.00',
            'expense_date': date.today().isoformat()
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_add_expense_missing_required_fields(self, client, admin_user):
        """
        TEST: Admin próbuje dodaś fakturę bez wymaganych pól -> walidacja
        """
        # zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #POST bez nazwy
        response = client.post('/admin/add-expense', data={
            'expense_name': '',
            'net_amount': '100',
            'vat_amount': '23',
            'expense_date': '2025-10-30'
        }, follow_redirects=True)

        assert response.status_code == 200
        # formularz powinien być wyświetlony z powrotem
        assert 'Dodaj fakturę kosztową' in response.data.decode('utf-8')

    def test_add_expense_back_dashboard(self, client, admin_user):
        """
        TEST: Stroda dodawania faktury ma link do dashboard
        """
        # zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        response = client.get('/admin/add-expense')

        assert response.status_code == 200
        assert '/admin/dashboard' in response.data.decode('utf-8')