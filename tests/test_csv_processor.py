"""
Testy dla modułu csv_processor
"""

import pytest
from io import BytesIO
from datetime import date
from app.csv_processor import CSVProcessor, CSVProcessorConfig
from app.models import User, BoltEarnings, UberEarnings


class TestPlatformDetection:
    """Testy wykrywania platformy na podstawie nazwy pliku"""

    def test_detect_bolt_by_keyword(self):
        """TEST: Wykrywa Bolt po słowie 'zarobki'"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "zarobki_kierowcy_01_01_2024.csv")
        assert processor.platform == 'bolt'

    def test_detect_bolt_by_date_pattern(self):
        """TEST: Wykrywa Bolt po wzorcu daty DD_MM_YYYY"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "raport_15_03_2024.csv")
        assert processor.platform == 'bolt'

    def test_detect_uber_by_keyword(self):
        """TEST: Wykrywa Uber po słowie 'payments'"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "payments_report_20240101-20240131.csv")
        assert processor.platform == 'uber'

    def test_detect_uber_by_date_pattern(self):
        """TEST: Wykrywa Uber po wzorcu daty YYYYMMDD-YYYYMMDD"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "20240101-20240131.csv")
        assert processor.platform == 'uber'

    def test_unknown_platform_raises_error(self):
        """TEST: Nieznany format pliku rzuca błąd"""
        file = BytesIO(b"dummy")
        with pytest.raises(ValueError, match="Nie można rozpoznać platformy"):
            CSVProcessor(file, "unknown_file.csv")


class TestDateExtraction:
    """Testy wyodrębniania daty z nazwy pliku"""

    def test_extract_bolt_date(self):
        """TEST: Wyodrębnia datę z formatu Bolt (DD_MM_YYYY)"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "zarobki_15_03_2024.csv")
        extracted_date = processor._extract_date_from_filename()
        assert extracted_date == date(2024, 3, 15)

    def test_extract_uber_date(self):
        """TEST: Wyodrębnia datę z formatu Uber (YYYYMMDD)"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "payments_20240315.csv")
        extracted_date = processor._extract_date_from_filename()
        assert extracted_date == date(2024, 3, 15)

    def test_fallback_to_today_if_no_date(self):
        """TEST: Zwraca dzisiejszą datę jeśli nie ma daty w nazwie"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "zarobki_test.csv")
        extracted_date = processor._extract_date_from_filename()
        assert extracted_date == date.today()


class TestVATCalculations:
    """Testy obliczeń VAT"""

    def test_calculate_bolt_vat(self):
        """TEST: Oblicza VAT dla Bolt"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "zarobki_01_01_2024.csv")
        
        row = {
            'brutto_app': 1000.0,      # 1000 * 0.08 = 80
            'brutto_cash': 500.0,       # 500 * 0.08 = 40
            'campaign': 100.0,          # 100 * 0.23 = 23
            'refunds': 50.0,            # 50 * 0.23 = 11.5
            'cancellations': 30.0,      # 30 * 0.23 = 6.9
            'expenses_total': 200.0     # 200 * 0.23 = 46 (odejmujemy)
        }
        
        vat = processor._calculate_bolt_vat(row)
        expected = 80 + 40 + 23 + 11.5 + 6.9 - 46
        assert abs(vat - expected) < 0.01

    def test_calculate_uber_vat(self):
        """TEST: Oblicza VAT dla Uber"""
        file = BytesIO(b"dummy")
        processor = CSVProcessor(file, "payments_20240101.csv")
        
        row = {
            'tax_on_fee': 50.0,
            'tax_general': 30.0,
            'tax_on_service_fee': 20.0
        }
        
        vat = processor._calculate_uber_vat(row)
        assert vat == 100.0


class TestUserLookup:
    """Testy wyszukiwania użytkowników"""

    def test_find_user_by_bolt_id(self, app, driver_user):
        """TEST: Znajduje użytkownika po bolt_id"""
        with app.app_context():
            from app import db
            from app.models import User
            
            # Pobierz użytkownika na nowo w tym kontekście
            user = User.query.get(driver_user.id)
            user.bolt_id = "BOLT123"
            db.session.commit()
            
            file = BytesIO(b"dummy")
            processor = CSVProcessor(file, "zarobki_01_01_2024.csv")
            
            row = {'platform_id': 'BOLT123'}
            found_user = processor._find_user(row)
            
            assert found_user is not None
            assert found_user.id == user.id


    def test_find_user_by_uber_id(self, app, driver_user):
        """TEST: Znajduje użytkownika po uber_id"""
        with app.app_context():
            from app import db
            from app.models import User
            
            # Pobierz użytkownika na nowo w tym kontekście
            user = User.query.get(driver_user.id)
            user.uber_id = "UBER456"
            db.session.commit()
            
            file = BytesIO(b"dummy")
            processor = CSVProcessor(file, "payments_20240101.csv")
            
            row = {'platform_id': 'UBER456'}
            found_user = processor._find_user(row)
            
            assert found_user is not None
            assert found_user.id == user.id

    def test_find_user_by_driver_name_fallback(self, app, driver_user):
        """TEST: Bolt fallback - znajduje po nazwie kierowcy"""
        with app.app_context():
            file = BytesIO(b"dummy")
            processor = CSVProcessor(file, "zarobki_01_01_2024.csv")
            
            row = {'driver_name': 'testdriver', 'platform_id': ''}
            found_user = processor._find_user(row)
            
            assert found_user is not None
            assert found_user.username == 'testdriver'

    def test_user_not_found_returns_none(self, app):
        """TEST: Zwraca None jeśli użytkownik nie istnieje"""
        with app.app_context():
            file = BytesIO(b"dummy")
            processor = CSVProcessor(file, "zarobki_01_01_2024.csv")
            
            row = {'platform_id': 'NONEXISTENT123'}
            found_user = processor._find_user(row)
            
            assert found_user is None


class TestBoltRecordCreation:
    """Testy tworzenia rekordów Bolt"""

    def test_create_bolt_record(self, app, driver_user):
        """TEST: Tworzy rekord BoltEarnings"""
        with app.app_context():
            driver_user.bolt_id = "BOLT123"
            from app import db
            db.session.commit()
            
            file = BytesIO(b"dummy")
            processor = CSVProcessor(file, "zarobki_01_01_2024.csv")
            
            row = {
                'gross_total': 1500.0,
                'expenses_total': 300.0,
                'net_income': 1200.0,
                'cash_collected': 500.0,
                'brutto_app': 1000.0,
                'brutto_cash': 500.0,
                'campaign': 0.0,
                'refunds': 0.0,
                'cancellations': 0.0
            }
            
            report_date = date(2024, 1, 1)
            record = processor._create_bolt_record(driver_user, row, report_date)
            
            assert record.user_id == driver_user.id
            assert record.bolt_id == "BOLT123"
            assert record.gross_total == 1500.0
            assert record.net_income == 1200.0
            assert record.cash_collected == 500.0
            assert record.report_date == report_date


class TestUberRecordCreation:
    """Testy tworzenia rekordów Uber"""

    def test_create_uber_record(self, app, driver_user):
        """TEST: Tworzy rekord UberEarnings"""
        with app.app_context():
            driver_user.uber_id = "UBER456"
            from app import db
            db.session.commit()
            
            file = BytesIO(b"dummy")
            processor = CSVProcessor(file, "payments_20240101.csv")
            
            row = {
                'gross_net_income': 1200.0,
                'service_fee': -200.0,
                'tax_on_service_fee': -50.0,
                'cash_collected': -300.0,
                'tax_on_fee': 30.0,
                'tax_general': 20.0
            }
            
            report_date = date(2024, 1, 1)
            record = processor._create_uber_record(driver_user, row, report_date)
            
            assert record.user_id == driver_user.id
            assert record.uber_id == "UBER456"
            assert record.gross_total == 1200.0
            assert record.net_income == 1200.0
            assert record.cash_collected == 300.0  # abs value
            assert record.report_date == report_date


class TestConfig:
    """Testy konfiguracji"""

    def test_bolt_config_exists(self):
        """TEST: Konfiguracja Bolt jest zdefiniowana"""
        config = CSVProcessorConfig.BOLT_CONFIG
        assert config['platform'] == 'bolt'
        assert 'column_mapping' in config
        assert 'numeric_columns' in config
        assert config['user_lookup_field'] == 'bolt_id'

    def test_uber_config_exists(self):
        """TEST: Konfiguracja Uber jest zdefiniowana"""
        config = CSVProcessorConfig.UBER_CONFIG
        assert config['platform'] == 'uber'
        assert 'column_mapping' in config
        assert 'numeric_columns' in config
        assert config['user_lookup_field'] == 'uber_id'