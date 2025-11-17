# Drivers Portal

Portal flotowy dla kierowców Uber i Bolt, napisany w Pythonie (Flask).  
Projekt powstał jako pomoc przy rozliczaniu kierowców w prowadzonej działalności gospodarczej oraz jako projekt portfolio.

## Status projektu

- Aktualna wersja: **0.42**
- Wersja z panelem admina, importem CSV i dodawaniem faktur kosztowych

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

## Testy

Projekt posiada kompleksowy zestaw testów

### Statystyki testów
- **61 testów** (wszystkie przechodzą)
- **70% pokrycia kodu**

## Jak uruchomić

### Wymagania
- Python 3.11+
- pip

### Instalacja

1. Sklonuj repozytorium:
```bash
git clone 
cd drivers-portal
```

2. Utwórz wirtualne środowisko:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

4. Utwórz plik `.env` z konfiguracją:
```
SECRET_KEY=twoj-tajny-klucz
DATABASE_URI=sqlite:///app.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

5. Zainicjuj bazę danych:
```bash
flask db upgrade
```

6. Utwórz konto administratora:
```bash
flask create-admin admin haslo123
```

7. Uruchom aplikację:
```bash
python run.py
```

Aplikacja będzie dostępna pod adresem: `http://localhost:5000`

### Uruchamianie testów
```bash
# Zainstaluj zależności deweloperskie
pip install pytest pytest-cov

# Uruchom testy
pytest

# Z pokryciem kodu
pytest --cov=app --cov-report=term-missing
```

## Technologie
- Python 3.11+
- Flask
- Flask-Login
- Flask-Migrate / Alembic
- SQLAlchemy
- WTForms
- Bootstrap 5
- Pandas (import CSV)
- pytest (testy)
- pytest-cov (pokrycie kodu)