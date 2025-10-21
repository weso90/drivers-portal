# Drivers Portal

Portal flotowy dla kierowców Uber i Bolt, napisany w Pythonie (Flask).  
Projekt powstał jako pomoc przy rozliczaniu kierowców w prowadzonej działalności gospodarczej oraz jako projekt portfolio.

## Status projektu

- Aktualna wersja: **0.4**
- Wersja MVP z panelem admina, importem CSV działa i dodawaniem faktur kosztowych

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
- możliwość dodawania faktur kosztowych kierowcy w celu obniżenia vatu

## W planach

  - rozbudowa panelu administratora i kierowcy
  - dodanie możliwości edycji i usuwania użytkownika
  - tworzenie raportów tygodniowych na podstawie rozliczeń

## Jak uruchomić
 --- DO UZUPEŁNIENIA ---

## Technologie
- Python 3.11+
- Flask
- Flask-Login
- Flask-Migrate / Alembic
- SQLAlchemy
- WTForms
- Bootstrap 5
- Pandas (import CSV)

## Historia zmian
Szczegóły w pliku [CHANGELOG.md](CHANGELOG.md).