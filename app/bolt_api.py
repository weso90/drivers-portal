import os
import requests
from flask import current_app
from datetime import datetime, time, timezone

BOLT_API_URL = "https://node.bolt.eu/fleet-integration-gateway"
BOLT_AUTH_URL = "https://oidc.bolt.eu/token"

def get_access_token():
    """Pobiera token dostępowy z API Bolta."""
    auth_url = BOLT_AUTH_URL
    client_id = os.environ.get('BOLT_CLIENT_ID')
    client_secret = os.environ.get('BOLT_CLIENT_SECRET')

    if not client_id or not client_secret:
        current_app.logger.error("Brak skonfigurowanych kluczy API Bolta.")
        return None

    auth_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "fleet-integration:api"
    }
    
    try:
        response = requests.post(auth_url, data=auth_data)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Błąd podczas autoryzacji w Bolt API: {e}")
        if e.response is not None:
            current_app.logger.error(f"Odpowiedź serwera Bolt: {e.response.text}")
        return None

def get_company_id(token):
    """Pobiera ID pierwszej dostępnej firmy."""
    if not token:
        return None
    
    companies_url = f"{BOLT_API_URL}/fleetIntegration/v1/getCompanies"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(companies_url, headers=headers)
        response.raise_for_status()
        
        if not response.text:
            current_app.logger.error("Odpowiedź z serwera Bolt była pusta.")
            return None

        companies_data = response.json().get("data", {})
        company_ids = companies_data.get("company_ids", [])
        
        if company_ids:
            return company_ids[0]
        else:
            current_app.logger.warning("Nie znaleziono żadnych firm dla tych danych API.")
            return None
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Błąd podczas pobierania firm z Bolt API: {e}")
        if e.response is not None:
            current_app.logger.error(f"Odpowiedź serwera Bolt: {e.response.text}")
        return None

def get_fleet_orders_for_day(report_date):
    """Pobiera wszystkie przejazdy floty dla danego dnia."""
    token = get_access_token()
    if not token:
        return None

    company_id = get_company_id(token)
    if not company_id:
        current_app.logger.error("Nie udało się pobrać company_id z API Bolta.")
        return None


    start_of_day_utc = datetime.combine(report_date, time.min, tzinfo=timezone.utc)
    end_of_day_utc = datetime.combine(report_date, time.max, tzinfo=timezone.utc)
    
    start_ts = int(start_of_day_utc.timestamp())
    end_ts = int(end_of_day_utc.timestamp())
    

    orders_url = f"{BOLT_API_URL}/fleetIntegration/v1/getFleetOrders"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    payload = {
        "company_id": company_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "limit": 1000,
        
    }

    try:
        response = requests.post(orders_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("data", {}).get("orders", [])
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Błąd podczas pobierania raportu z Bolt API: {e}")
        if e.response is not None:
            current_app.logger.error(f"Odpowiedź serwera Bolt: {e.response.text}")
        return None