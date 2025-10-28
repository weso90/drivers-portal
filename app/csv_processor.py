"""
Moduł do przetwarzania plików CSV z platform Uber i Bolt.
Automatycznie rozpoznaje typ platformy i przetwarza dane.
"""

from app import db
from app.models import User, BoltEarnings, UberEarnings
import pandas as pd
import re
from datetime import datetime
from decimal import Decimal

class CSVProcessorConfig:
    """
    Konfiguracja dla różnych platform.
    """

    BOLT_CONFIG = {
        'platform': 'bolt',
        'column_mapping': {
            "Kierowca": "driver_name",
            "Identyfikator kierowcy": "platform_id",
            "Zarobki brutto (ogółem)|ZŁ": "gross_total",
            "Opłaty ogółem|ZŁ": "expenses_total",
            "Zarobki netto|ZŁ": "net_income",
            "Pobrana gotówka|ZŁ": "cash_collected",
            "Zarobki brutto (płatności w aplikacji)|ZŁ": "brutto_app",
            "Zarobki brutto (płatności gotówkowe)|ZŁ": "brutto_cash",
            "Zarobki z kampanii|ZŁ": "campaign",
            "Zwroty wydatków|ZŁ": "refunds",
            "Opłaty za anulowanie|ZŁ": "cancellations"
        },
        'numeric_columns': ["gross_total", "expenses_total", "net_income", "cash_collected", "brutto_app", "brutto_cash", "campaign", "refunds", "cancellations"],
        'user_lookup_field': 'bolt_id',
        'model': BoltEarnings
    }

    UBER_CONFIG = {
        'platform': 'uber',
        'column_mapping': {
            "Identyfikator UUID kierowcy": "platform_id",
            "Imię kierowcy": "first_name",
            "Nazwisko kierowcy": "last_name",
            "Wypłacono Ci : Twój przychód": "gross_net_income",
            "Wypłacono Ci : Bilans przejazdu : Wypłaty : Odebrana gotówka": "cash_collected",
            "Wypłacono Ci:Twój przychód:Opłata za usługę": "service_fee",
            "Wypłacono Ci:Twój przychód:Opłata:Podatek od opłaty": "tax_on_fee",
            "Wypłacono Ci:Twój przychód:Podatki:Podatek": "tax_general",
            "Wypłacono Ci:Twój przychód:Podatki:Podatek od opłaty za usługę": "tax_on_service_fee"
        },
        'numeric_columns': ["gross_net_income", "cash_collected", "service_fee", "tax_on_fee", "tax_general", "tax_on_service_fee"],
        'user_lookup_field': 'uber_id',
        'model': UberEarnings
    }

class CSVProcessor:
    """
    Procesor plików CSV - rozpoznaje platformę i przetwarza dane
    """

    def __init__(self, file, filename):
        """
        Args:
            file: FileStorage object z formularza
            filename: nazwa pliku
        """
        self.file = file
        self.filename = filename
        self.platform = self._detect_platform()
        self.config = self._get_config()

    def _detect_platform(self):
        """
        Automatycznie rozpoznaje platformę na podstawie nazwy pliku.

        Returns:
            str: 'bolt' lub 'uber'
        Raises:
            ValueError: jeśli nie można rozpoznać platformy
        """
        filename_lower = self.filename.lower()

        # Sprawdź wzorce charakterystyczne dla każdej platformy
        if 'zarobki' in filename_lower or re.search(r'\d{2}_\d{2}_\d{4}', self.filename):
            return 'bolt'
        elif 'payments' in filename_lower or re.search(r'\d{8}-\d{8}', self.filename):
            return 'uber'
        else:
            raise ValueError(
                f"Nie można rozpoznać platformy dla pliku: {self.filename}. "
                "Plik powinien zawierać 'zarobki' (Bolt) lub 'payments' (Uber)"
            )
        
    def _get_config(self):
        """
        Zwraca konfigurację dla rozpoznanej platformy
        """
        if self.platform == 'bolt':
            return CSVProcessorConfig.BOLT_CONFIG
        elif self.platform == 'uber':
            return CSVProcessorConfig.UBER_CONFIG
        else:
            raise ValueError(f"Nieznana platforma: {self.platform}")
        
    def _extract_date_from_filename(self):
        """
        Wyszukuje datę w nazwie pliku.
        Obsługuje formaty Bolt (DD_MM_YYYY) i Uber (YYYYMMDD).
        """
        # Uber format: YYYYMMDD
        m = re.search(r'(\d{8})', self.filename)
        if m:
            try:
                return datetime.strptime(m.group(1), "%Y%m%d").date()
            except ValueError:
                pass

        # Bolt format: DD_MM_YYYY
        m = re.search(r'(\d{2}_\d{2}_\d{4})', self.filename)
        if m:
            try:
                return datetime.strptime(m.group(1), "%d_%m_%Y").date()
            except ValueError:
                pass
        
        # Fallback
        return datetime.utcnow().date()
    
    def _load_csv(self):
        """
        Wczytuje CSV do DataFrame
        """

        try:
            df = pd.read_csv(self.file, sep=None, engine='python', encoding='utf-8-sig')
        except Exception:
            self.file.seek(0)
            df = pd.read_csv(self.file, sep=',', engine='python', encoding='utf-8-sig')
        return df

    def _map_columns(self, df):
        """
        Mapuje kolumny CSV na standardowe nazwy
        """

        column_mapping = self.config['column_mapping']

        # Wybierz tylko kolumny które istnieją
        present_columns = [col for col in column_mapping if col in df.columns]
        df = df[present_columns].copy()
        df.rename(columns=column_mapping, inplace=True)

        # Konwersja na float, brakujące = 0.0
        for col in self.config['numeric_columns']:
            if col in df.columns:
                df[col] = df[col].fillna(0.0).astype(float)
            else:
                df[col] = 0.0
        return df
    
    def _find_user(self, row):
        """
        Znajduje użytkownika w bazie na podstawie danych z CSV

        Args:
            row: wiersz DataFrame
        Returns:
            User lub None
        """

        user = None
        lookup_field = self.config['user_lookup_field']

        # Szukaj po platform_id (bolt_id lub uber_id)
        if 'platform_id' in row and str(row['platform_id']).strip():
            platform_id_value = str(row['platform_id']).strip()
            if platform_id_value.lower() != 'nan':
                user = User.query.filter_by(**{lookup_field: platform_id_value}).first()

        # Fallback dla Bolt: szukaj po nazwie kierowcy
        if user is None and self.platform == 'bolt' and 'driver_name' in row:
            driver_name = str(row['driver_name']).strip()
            if driver_name:
                user = User.query.filter_by(username=driver_name).first()

        # Fallback dla Uber: szukaj po imię + nazwisko
        if user is None and self.platform == 'uber':
            if 'first_name' in row and 'last_name' in row:
                full_name = f"{row['first_name']} {row['last_name']}".strip()
                user = User.query.filter_by(username=full_name).first()

        return user
    
    def _calculate_bolt_vat(self, row):
        """
        Oblicza VAT dla Bolt
        """

        vat_due = (
            row.get("brutto_app", 0.0) * 0.08 +
            row.get("brutto_cash", 0.0) * 0.08 +
            row.get("campaign", 0.0) * 0.23 +
            row.get("refunds", 0.0) * 0.23 +
            row.get("cancellations", 0.0) * 0.23
        ) - row.get("expenses_total", 0.0) * 0.23

        return vat_due
    
    def _calculate_uber_vat(self, row):
        """
        Oblicza VAT dla Uber
        """

        vat_due = (
            float(row.get("tax_on_fee", 0.0)) +
            float(row.get("tax_general", 0.0)) +
            float(row.get("tax_on_service_fee", 0.0))
        )

        return vat_due
    
    def _create_bolt_record(self, user, row, report_date):
        """
        Tworzy rekord BoltEarnings
        """

        vat_due = self._calculate_bolt_vat(row)
        net_income = float(row.get("net_income", 0.0))
        actual_income = net_income - vat_due

        return BoltEarnings(
            user_id=user.id,
            bolt_id=user.bolt_id,
            report_date=report_date,
            gross_total=float(row.get("gross_total", 0.0)),
            expenses_total=float(row.get("expenses_total", 0.0)),
            net_income=net_income,
            cash_collected=float(row.get("cash_collected", 0.0)),
            vat_due=vat_due,
            actual_income=actual_income
        )
    
    def _create_uber_record(self, user, row, report_date):
        """
        Tworzy rekord UberEarnings
        """

        gross_total = float(row.get("gross_net_income", 0.0))
        expenses_total = abs(
            float(row.get("service_fee", 0.0)) +
            float(row.get("tax_on_service_fee", 0.0))
        )
        net_income = float(row.get("gross_net_income", 0.0))
        cash_collected = abs(float(row.get("cash_collected", 0.0)))
        vat_due = self._calculate_uber_vat(row)
        actual_income = net_income - vat_due

        return UberEarnings(
            user_id=user.id,
            uber_id=user.uber_id,
            report_date=report_date,
            gross_total=gross_total,
            expenses_total=expenses_total,
            net_income=net_income,
            cash_collected=cash_collected,
            vat_due=vat_due,
            actual_income=actual_income
        )
    
    def _update_record(self, existing, row):
        """
        Aktualizuje istniejący rekord
        """

        if self.platform == 'bolt':
            vat_due = self._calculate_bolt_vat(row)
            net_income = float(row.get("net_income", 0.0))
            
            existing.gross_total = float(row.get("gross_total", 0.0))
            existing.expenses_total = float(row.get("expenses_total", 0.0))
            existing.net_income = net_income
            existing.cash_collected = float(row.get("cash_collected", 0.0))
            existing.vat_due = vat_due
            existing.actual_income = net_income - vat_due
            
        elif self.platform == 'uber':
            gross_total = float(row.get("gross_net_income", 0.0))
            expenses_total = abs(
                float(row.get("service_fee", 0.0)) +
                float(row.get("tax_on_service_fee", 0.0))
            )
            net_income = float(row.get("gross_net_income", 0.0))
            cash_collected = abs(float(row.get("cash_collected", 0.0)))
            vat_due = self._calculate_uber_vat(row)
            
            existing.gross_total = gross_total
            existing.expenses_total = expenses_total
            existing.net_income = net_income
            existing.cash_collected = cash_collected
            existing.vat_due = vat_due
            existing.actual_income = net_income - vat_due

    def process(self):
        """
        Główna metoda przetwarzania CSV.

        returns:
        dict: {'created': int, 'updated': int, 'skipped': int, 'platform': str}
        """

        # Wczytaj i przekształć dane
        df = self._load_csv()
        df = self._map_columns(df)
        report_date = self._extract_date_from_filename()
        df["report_date"] = report_date

        # Statystyki
        created, updated, skipped = 0, 0, 0
        Model = self.config['model']

        # Przetwórz każdy wiersz
        for _, row in df.iterrows():
            user = self._find_user(row)

            if user is None:
                skipped += 1
                continue

            # sprawdź czy rekord istnieje
            existing = Model.query.filter_by(
                user_id=user.id,
                report_date=report_date
            ).first()

            if existing is None:
                # Utwórz nowy rekord
                if self.platform == 'bolt':
                    record = self._create_bolt_record(user, row, report_date)
                else:
                    record = self._create_uber_record(user, row, report_date)

                db.session.add(record)
                created += 1
            else:
                # zaktualizuj istniejący
                self._update_record(existing, row)
                updated += 1
        
        db.session.commit()

        return {
            'created': created,
            'updated': updated,
            'skipped': skipped,
            'platform': self.platform
        }