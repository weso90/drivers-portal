# Drivers Portal

Portal flotowy dla kierowców Uber i Bolt, napisany w Pythonie (Flask).  
Projekt powstał jako nauka i jednocześnie demo do portfolio oraz jako wartość użytkowa przy prowadzeniu działalności gospodarczej

## Status projektu

- Aktualna wersja: **0.2**
- Wersja MVP z panelem admina i importem CSV działa.
- W planach:
  - integracja z Uber - jeszcze nie wiem czy api czy import csv
  - rozbudowa panelu administratora i kierowcy
  - dodanie możliwości edycji i usuwania użytkownika
  - możliwość dodawania faktur kosztowych kierowcy w celu obniżenia vatu
  - tworzenie raportów tygodniowych na podstawie rozliczeń

## Funkcjonalności

- Logowanie kierowcy i administratora (Flask-Login)
- Panel administratora:
  - dodawanie kierowców (z przypisanym `uber_id` i `bolt_id`)
  - import raportów zarobków z plików CSV (Bolt)
- Automatyczne obliczanie podatków (VAT) i faktycznych zarobków kierowców
- Dane zapisywane w bazie SQLite (z migracjami Alembic / Flask-Migrate)
- Szablony HTML w oparciu o Bootstrap 5:
  - wspólny layout `base.html`
  - oddzielne widoki dla admina i kierowcy
- Hasła przechowywane w postaci hashy (Werkzeug)

## Struktura projektu
drivers-portal/
│── run.py # punkt startowy aplikacji
│── requirements.txt # zależności
│── app/
│ ├── init.py # konfiguracja aplikacji, bazy, logowania
│ ├── models.py # modele bazy danych (User, BoltEarnings)
│ ├── routes.py # trasy aplikacji (admin, kierowcy, CSV upload)
│ ├── forms.py # formularze (login, dodanie kierowcy, CSV upload)
│ ├── commands.py # dodatkowe komendy CLI (np. create-admin)
│ ├── templates/ # szablony HTML (admin/, driver/, base.html)
│ └── app.db # baza danych SQLite (lokalnie)

## Jak uruchomić
 --- DO UZUPEŁNIENIA ---

## Technologie
Python 3.11+
Flask
Flask-Login
Flask-Migrate / Alembic
SQLAlchemy
WTForms
Bootstrap 5
Pandas (import CSV)

## Historia zmian
Szczegóły w pliku [CHANGELOG.md](CHANGELOG.md).