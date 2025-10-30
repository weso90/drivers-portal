"""
Testy blueprintu Auth (logowanie, wylogowanie)
"""

import pytest
from app.models import User

class TestAuthBlueprint:
    """
    Testy autentykacji użytkowników
    """
    def test_login_page_loads(self, client):
        """
        TEST: Strona logowania się ładuje
        """
        response = client.get('/login')

        assert response.status_code == 200
        assert 'Panel logowania' in response.data.decode('utf-8')
        assert 'Nazwa użytkownika' in response.data.decode('utf-8')

    def test_login_with_valid_admin_credentials(self, client, admin_user):
        """
        TEST: Admin loguje się poprawnymi danymi -> przekierowanie na /admin/dashboard
        """
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert 'Panel Administratora' in response.data.decode('utf-8')
        assert 'Dodaj nowego kierowcę' in response.data.decode('utf-8')

    def test_login_with_valid_driver_credentials(self, client, driver_user):
        """
        TEST: Kierowca loguje się poprawnymi danymi -> przekierowanie na /driver/dashboard
        """
        response = client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert 'Panel Kierowcy' in response.data.decode('utf-8')
        assert 'Witaj, testdriver' in response.data.decode('utf-8')

    def test_login_with_invalid_credentials(self, client):
        """
        TEST: Logowanie ze złymi danymi -> komunikat błędu
        """
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'wrongpass'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert 'Nieprawidłowe dane logowania' in response.data.decode('utf-8')
        assert 'Panel logowania' in response.data.decode('utf-8')

    def test_login_with_missing_username(self, client):
        """
        TEST: Logowanie bez username -> walidacja formularza
        """
        response = client.post('/login', data={
            'username': '',
            'password': 'pass'
        }, follow_redirects=True)

        assert response.status_code == 200
        # formularz powinien pokazać błąd walidacji
        assert 'Panel logowania' in response.data.decode('utf-8')

    def test_logout(self, client, admin_user):
        """
        TEST: Wylogowanie -> przekierowanie na /login z komunikatem
        """
        #najpierw zaloguj
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #teraz wyloguj
        response = client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        assert 'Zostałeś poprawnie wylogowany' in response.data.decode('utf-8')
        assert 'Panel logowania' in response.data.decode('utf-8')

    def test_already_logged_in_admin_redirects_to_dashboard(self, client, admin_user):
        """
        TEST: Zalogowany admin wchodzi na /login -> przekierowanie na /admin/dashboard
        """
        #zaloguj się
        client.post('login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #spróbuj wejść na /login
        response = client.get('/login', follow_redirects=True)

        assert response.status_code == 200
        assert 'Panel Administratora' in response.data.decode('utf-8')

    def test_already_logged_in_driver_redirects_to_dashboard(self, client, driver_user):
        """
        TEST: Zalogowany kierowca wchodzi na /login -> przekierowanie na /driver/dashboard
        """
        #zaloguj się
        client.post('login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        #spróbuj wejść na /login
        response = client.get('/login', follow_redirects=True)

        assert response.status_code == 200
        assert 'Panel Kierowcy' in response.data.decode('utf-8')

    def test_root_url_redirects_to_login(self, client):
        """
        TEST: Niezalogowany user '/' -> przekierowanie na /login
        """
        response = client.get('/', follow_redirects=True)

        assert response.status_code == 200
        assert 'Panel logowania' in response.data.decode('utf-8')