# Changelog

Wszystkie istotne zmiany w tym projekcie będą dokumentowane w tym pliku.

---


## [0.41] - 2025-10-28
### Zmienione
- refactor kodu:
 - stworzenie klasy CSVProcessor z auto detekcją czy to uber czy bolt na podstawie nazwy pliku
 - konfigurowalne mapowanie kolumn zależnie od platformy
 - łatwa rozbudowa o nowe platformy
 - redukcja powtarzania kodu o około 70%

---

## [0.4] - 2025-10-21
### Dodane
- możliwość dodawania faktur kosztowych kierowcy w celu obniżenia vatu

---


## [0.3] - 2025-10-19
### Dodane
- dodanie importu danych z pliku CSV Ubera
- Dodanie widoku zarobków dla administratora
- wybieranie zakresu dat do zarobków

---


## [0.22] - 2025-10-18
### Zmienione
- wrażliwe dane przeniesione do pliku .env
- zmiana danych w sql z float na numeric

---

## [0.21] - 2025-09-20
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