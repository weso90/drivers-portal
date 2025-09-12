# test_bolt_api.py
import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, time, timezone, timedelta

load_dotenv()

BOLT_API_URL = "https://node.bolt.eu/fleet-integration-gateway"
BOLT_AUTH_URL = "https://oidc.bolt.eu/token"

def get_access_token():
    """Pobiera token autoryzacyjny."""
    client_id = os.environ.get('BOLT_CLIENT_ID')
    client_secret = os.environ.get('BOLT_CLIENT_SECRET')
    auth_data = {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret, "scope": "fleet-integration:api"}
    try:
        response = requests.post(BOLT_AUTH_URL, data=auth_data)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception: return None

def get_company_id(token):
    """Pobiera ID firmy."""
    companies_url = f"{BOLT_API_URL}/fleetIntegration/v1/getCompanies"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        response = requests.get(companies_url, headers=headers)
        response.raise_for_status()
        company_ids = response.json().get("data", {}).get("company_ids", [])
        return company_ids[0] if company_ids else None
    except Exception: return None

def test_get_fleet_orders(token, company_id):
    """(ZAKTUALIZOWANA FUNKCJA) Odpytuje /getFleetOrders z WSZYSTKIMI parametrami."""
    print(f"\n--- KROK 2: Próba odpytania /getFleetOrders z pełnym payloadem ---")
    
    orders_url = f"{BOLT_API_URL}/fleetIntegration/v1/getFleetOrders"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # Ustawiamy zakres dat na ostatnie 12 dni, co działało dla /getDrivers
    end_date = datetime.now()
    start_date = end_date - timedelta(days=12)
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())
    
    # === TWORZYMY PAYLOAD ZAWIERAJĄCY WSZYSTKIE MOŻLIWE PARAMETRY ===
    payload = {
        "company_id": company_id,
        "company_ids": [company_id],
        "start_ts": start_ts,
        "end_ts": end_ts,
        "limit": 1000,
        "offset": 0,
    }
    # ================================================================

    print(f"Wysyłam zapytanie POST na adres: {orders_url}")
    print(f"Z payloadem: {json.dumps(payload)}")

    try:
        response = requests.post(orders_url, headers=headers, json=payload)
        
        print("\n--- ANALIZA ODPOWIEDZI SERWERA ---")
        print(f"Status odpowiedzi: {response.status_code}")
        print(f"Typ zawartości (Content-Type): {response.headers.get('Content-Type')}")
        print("--- Treść odpowiedzi ---")
        parsed_response = json.loads(response.text)
        print(json.dumps(parsed_response, indent=2, ensure_ascii=False))
        print("--------------------------")

    except Exception as e:
        print(f"BŁĄD KRYTYCZNY: {e}")

if __name__ == "__main__":
    access_token = get_access_token()
    if access_token:
        print("SUKCES: Otrzymano token.")
        company_id = get_company_id(access_token)
        if company_id:
            print(f"SUKCES: Otrzymano company_id: {company_id}")
            test_get_fleet_orders(access_token, company_id)
        else:
            print("Nie udało się uzyskać ID firmy. Koniec testu.")
    else:
        print("Nie udało się uzyskać tokenu. Test przerwany.")