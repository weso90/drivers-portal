import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, time, timezone


load_dotenv()


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
    except:
        return None

def get_company_id(token):
    """Pobiera ID firmy."""
    companies_url = f"{BOLT_API_URL}/fleetIntegration/v1/getCompanies"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        response = requests.get(companies_url, headers=headers)
        response.raise_for_status()
        companies_data = response.json().get("data", {})
        company_ids = companies_data.get("company_ids", [])
        if company_ids:
            return company_ids[0]
        return None
    except:
        return None

def get_fleet_orders_for_range(start_date, end_date):
    """Pobiera wszystkie przejazdy floty dla danego zakresu dat."""
    token = get_access_token()
    if not token: 
        print("BŁĄD: Nie udało się uzyskać tokenu.")
        return None
    
    company_id = get_company_id(token)
    if not company_id: 
        print("BŁĄD: Nie udało się uzyskać ID firmy.")
        return None
        
    start_of_period_utc = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_of_period_utc = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    start_ts = int(start_of_period_utc.timestamp())
    end_ts = int(end_of_period_utc.timestamp())
    
    orders_url = f"{BOLT_API_URL}/fleetIntegration/v1/getFleetOrders"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    payload = {"company_id": company_id, "start_ts": start_ts, "end_ts": end_ts, "limit": 1000}
    
    try:
        response = requests.post(orders_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("data", {}).get("orders", [])
    except Exception as e:
        print(f"BŁĄD podczas pobierania przejazdów: {e}")
        return None

if __name__ == "__main__":
    start_date = datetime(2025, 9, 3).date()
    end_date = datetime(2025, 9, 4).date()
    
    print(f"--- Start testu dla zakresu dat: od {start_date.strftime('%Y-%m-%d')} do {end_date.strftime('%Y-%m-%d')} ---")
    
    orders = get_fleet_orders_for_range(start_date, end_date)
    
    print("\n--- WYNIK TESTU ---")
    if orders is None:
        print("BŁĄD: Zapytanie do API nie powiodło się lub wystąpił inny błąd.")
    else:
        print(f"Znaleziono przejazdów: {len(orders)}")
        if len(orders) > 0:
            print("--- Pobrane dane (pierwszy przejazd) ---")
            print(json.dumps(orders[0], indent=2, ensure_ascii=False))
        else:
            print("Lista przejazdów jest pusta.")
    print("-------------------")