import os
import requests
from flask import current_app
from datetime import datetime, time, timezone, timedelta

BOLT_API_URL = "https://node.bolt.eu/fleet-integration-gateway"
BOLT_AUTH_URL = "https://oidc.bolt.eu/token"

def get_access_token():
    """Pobiera token autoryzacyjny."""
    client_id = os.environ.get('BOLT_CLIENT_ID')
    client_secret = os.environ.get('BOLT_CLIENT_SECRET')
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "fleet-integration:api"
    }
    try:
        response = requests.post(BOLT_AUTH_URL, data=auth_data)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Błąd podczas autoryzacji w Bolt API: {e}")
        if e.response is not None:
            current_app.logger.error(f"Odpowiedź serwera Bolt: {e.response.text}")
        return None

def get_company_id(token):
    """Pobiera ID firmy."""
    companies_url = f"{BOLT_API_URL}/fleetIntegration/v1/getCompanies"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        response = requests.get(companies_url, headers=headers)
        response.raise_for_status()
        company_ids = response.json().get("data", {}).get("company_ids", [])
        return company_ids[0] if company_ids else None
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Błąd podczas pobierania firm z Bolt API: {e}")
        if e.response is not None:
            current_app.logger.error(f"Odpowiedź serwera Bolt: {e.response.text}")
        return None

def get_fleet_orders_for_range(start_date, end_date):
    """Pobiera WSZYSTKIE przejazdy floty, używając ostatecznej, poprawionej wersji payload."""
    token = get_access_token()
    if not token: 
        return None

    company_id = get_company_id(token)
    if not company_id:
        current_app.logger.error("Nie udało się pobrać company_id z API Bolta.")
        return None

    # === ZAKTUALIZOWANA LOGIKA DAT ZGODNIE Z TWOJĄ PROŚBĄ ===
    start_of_period_utc = datetime.combine(start_date, time(0, 0, 0), tzinfo=timezone.utc)
    end_of_period_utc = datetime.combine(end_date, time(23, 59, 59), tzinfo=timezone.utc)
    start_ts = int(start_of_period_utc.timestamp())
    end_ts = int(end_of_period_utc.timestamp())
    # =======================================================

    orders_url = f"{BOLT_API_URL}/fleetIntegration/v1/getFleetOrders"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    all_orders = []
    offset = 0
    limit = 1000

    while True:
        payload = {
            "company_id": company_id,
            "company_ids": [company_id],
            "start_ts": start_ts,
            "end_ts": end_ts,
            "limit": limit,
            "offset": offset,
            "time_range_filter_type": "price_review"
        }
        
        try:
            response = requests.post(orders_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json().get("data", {})
            orders_on_page = response_data.get("orders", [])
            
            if not orders_on_page:
                break

            all_orders.extend(orders_on_page)
            offset += len(orders_on_page)

            # API zwraca pole total_orders tylko na pierwszej stronie, ale
            # pętla i tak zakończy się poprawnie, gdy nie będzie już wyników
            total_orders = response_data.get("total_orders")
            if total_orders is not None and len(all_orders) >= total_orders:
                break

        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Błąd podczas pobierania raportu z Bolt API (offset: {offset}): {e}")
            if e.response is not None:
                current_app.logger.error(f"Odpowiedź serwera Bolt: {e.response.text}")
            return None

    return all_orders
