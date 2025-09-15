import pandas as pd
import re
from datetime import datetime

def extract_date_from_filename(filename: str):
    match = re.search(r"\d{2}_\d{2}_\d{4}", filename)
    if not match:
        raise ValueError("Nie znaleziono daty w nazwie pliku!")
    raw_date = match.group()
    return datetime.strptime(raw_date, "%d_%m_%Y").date()

def load_selected_columns(csv_path: str):
    columns = [
        "Zarobki brutto (ogółem)|ZŁ",
        "Zarobki brutto (płatności w aplikacji)|ZŁ",
        "Zarobki brutto (płatności gotówkowe)|ZŁ",
        "Pobrana gotówka|ZŁ",
        "Napiwki od pasażerów|ZŁ",
        "Zarobki z kampanii|ZŁ",
        "Zwroty wydatków|ZŁ",
        "Opłaty za anulowanie|ZŁ",
        "Opłaty ogółem|ZŁ",
        "Zarobki netto|ZŁ",
    ]
    
    # wczytanie CSV
    df = pd.read_csv(csv_path, sep=",", encoding="utf-8")
    df = df[columns]
    
    # dodajemy kolumnę report_date
    report_date = extract_date_from_filename(csv_path)
    df["report_date"] = report_date
    
    return df

# test użycia
if __name__ == "__main__":
    path = "Zarobki na kierowcę-13_09_2025-13_09_2025-plik.csv"
    df = load_selected_columns(path)
    print(df.head())