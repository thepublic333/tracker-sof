import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime
from collections import defaultdict
import time
import pycountry
import re

# === 1. Load Google Sheets credentials ===
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

# === 2. Setup sheet handles ===
sheet = client.open("Sofwave Provider Data")
log_sheet = sheet.worksheet("Log")
summary_sheet = sheet.worksheet("DailySummary")

# === 3. Country normalization ===
def normalize_country(code_or_name):
    if not code_or_name or not isinstance(code_or_name, str):
        return "Null"
    code = code_or_name.strip().upper()
    try:
        country = pycountry.countries.get(alpha_2=code) or pycountry.countries.get(alpha_3=code)
        if country:
            return country.name
    except:
        pass
    try:
        return pycountry.countries.lookup(code).name
    except:
        return "Null"

# === 4. Extract upload date from logo URL ===
def extract_logo_upload_date(url: str) -> str:
    match = re.search(r'/(\d{4})/(\d{2})/', url)
    if match:
        year, month = match.groups()
        return f"{year}-{month}"
    return "Null"

# === 5. Helpers ===
def get_existing_provider_names():
    records = log_sheet.get_all_records()
    return set(row['Name'] for row in records)

def update_country_headers(existing_headers, today_country_counts):
    updated = False
    for country in today_country_counts:
        if country not in existing_headers:
            existing_headers.append(country)
            updated = True
    if updated:
        summary_sheet.resize(rows=summary_sheet.row_count, cols=len(existing_headers))
        summary_sheet.update("A1", [existing_headers])
    return existing_headers

# === 6. Scrape Sofwave API ===
time.sleep(3)  # simulate human delay

url = "https://api.sofwave.com/wp-json/cherami/v1/provider"
params = {
    "is_resume": "true",
    "long": 65.7067,
    "lat": 0.0000,
    "bounds[sw_lat]": -85.05112900000003,
    "bounds[sw_long]": -280.70361507963156,
    "bounds[ne_lat]": 85.05112877980659,
    "bounds[ne_long]": 412.1170412711306
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Referer": "https://sofwave.com/",
    "Origin": "https://sofwave.com",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

response = requests.get(url, headers=headers, params=params, timeout=60)
data = response.json()
providers = data.get("items", [])

print(f"✅ Retrieved {len(providers)} providers")

# === 7. Diff + log ===
today = datetime.utcnow().strftime("%Y-%m-%d")
existing_names = get_existing_provider_names()

new_providers = []
country_counts = defaultdict(int)

# Ensure headers are present in the log sheet
if not log_sheet.row_values(1):
    log_sheet.append_row(["Date", "Name", "Country", "Address", "Logo Upload Date"])

for provider in providers:
    name = provider.get("title", "N/A")
    billing = provider.get("billing", {})
    raw_country = billing.get("country", None)
    country = normalize_country(raw_country)
    address = billing.get("address", "N/A")
    logo_url = provider.get("informations", {}).get("logo", {}).get("url", "")
    logo_upload_date = extract_logo_upload_date(logo_url)

    if name not in existing_names:
        new_providers.append([today, name, country, address, logo_upload_date])
        country_counts[country] += 1

# Append new entries to log
if new_providers:
    log_sheet.append_rows(new_providers)

# === 8. Update summary ===
existing_headers = summary_sheet.row_values(1)
if not existing_headers:
    existing_headers = ["Date", "Total Providers", "New Providers"]

# Expand country columns if needed
existing_headers = update_country_headers(existing_headers, country_counts)

# Prepare summary row
summary_row = [today, len(providers), len(new_providers)]
for country in existing_headers[3:]:  # skip Date, Total, New
    summary_row.append(country_counts.get(country, 0))

summary_sheet.append_row(summary_row)

print(f"📊 Summary updated: {summary_row}")
