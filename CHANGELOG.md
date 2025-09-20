# Changelog

Wszystkie istotne zmiany w tym projekcie będą dokumentowane w tym pliku.





---

## [0.21] - 2025-09-18
### Zmienione
- usunięte stare pliki login (admin/driver) - zastąpione jednym wspólnym

---

## [0.2] - 2025-09-18
### Dodane
- Import plików CSV z raportami Bolt.
- Automatyczne obliczanie VAT i faktycznego zarobku.
- Formularz `CSVUploadForm` i widok `upload_csv`.
- Przycisk w panelu admina do importu danych.
- Nowy model `BoltEarnings` w bazie danych.

---

## [0.1] - 2025-09-10
### Dodane
- Podstawowa obsługa użytkowników (kierowca i administrator).
- Logowanie i wylogowanie (Flask-Login).
- Dodawanie kierowców w panelu admina.
- Hasła zapisywane w postaci hashy.
- Struktura bazy danych oparta na SQLAlchemy.