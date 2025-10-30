"""
Testy blueprintu Driver (panel kierowcy)
"""
import pytest
from app.models import User

class TestDriverBlueprint:
    """
    Test panelu kierowcy
    """
    def test_driver_dashboard_requires_login(self, client):
        """
        TEST: Niezalogowany user próbuje wejść na /driver/dashboard -> redirect na /login
        """
        response = client.get('/driver/dashboard')

        #sprawdź redirect (302)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_driver_can_access_own_dashboard(self, client, driver_user):
        """
        TEST: Zalogowany kierowca wchodzi na swój dashboard -> sukces
        """
        #zaloguj się jako kierowca
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        #wejdź na dashboard
        response = client.get('/driver/dashboard')

        assert response.status_code == 200
        assert 'Panel Kierowcy' in response.data.decode('utf-8')
        assert 'Witaj, testdriver' in response.data.decode('utf-8')

    def test_admin_cannot_access_driver_dashboard(self, client, admin_user):
        """
        TEST: Admin próbuje wejść na /driver/dashboard -> brak uprawnień
        """
        #zaloguj się jako admin
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })

        #spróbuj wejść na driver dashboard
        response = client.get('/driver/dashboard', follow_redirects=True)

        assert response.status_code == 200
        assert 'Brak uprawnień' in response.data.decode('utf-8')
        #powinien być z powrotem na stronie logowania
        assert 'Panel Administratora' in response.data.decode('utf-8')

    def test_driver_dashboard_shows_no_earnings_message(self, client, driver_user):
        """
        TEST: Kierowca bez zarobków widzi komunikat "Brak danych"
        """
        # zaloguj się jako kierowca
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        #wejdź na dashboard
        response = client.get('/driver/dashboard')

        assert response.status_code == 200
        assert 'Brak danych o zarobkach' in response.data.decode('utf-8')

    def test_driver_dashboard_displays_username(self, client, driver_user):
        """
        TEST: Dashboard wyświetla poprawną nazwę użytkownika
        """
        #zaloguj się
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        response = client.get('/driver/dashboard')

        assert response.status_code == 200
        #sprawdź czy wyświetla nazwę użytkownika
        assert driver_user.username in response.data.decode('utf-8')

    def test_driver_sees_logout_link(self, client, driver_user):
        """
        TEST: Zalogowany kierowca widzi przycisk "Wyloguj" w navbar
        """
        #zaloguj się
        client.post('/login', data={
            'username': 'testdriver',
            'password': 'driver123'
        })

        response = client.get('/driver/dashboard')

        assert response.status_code == 200
        assert 'Wyloguj' in response.data.decode('utf-8')
        assert '/logout' in response.data.decode('utf-8')