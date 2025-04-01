import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime
from collections import defaultdict
import time
import pycountry

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

# === 4. Helpers ===
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

def extract_logo_upload_date(url):
    try:
        parts = url.split("/")
        year_index = parts.index("uploads") + 1
        year = parts[year_index]
        month = parts[year_index + 1]
        return f"{year}-{month}-01"
    except:
        return "Null"

# === 5. Scrape Sofwave API ===
time.sleep(3)

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

# === 6. Diff + log ===
today = datetime.utcnow().strftime("%Y-%m-%d")
existing_names = get_existing_provider_names()

new_providers = []
country_counts = defaultdict(int)

for provider in providers:
    name = provider.get("title", "N/A")
    billing = provider.get("billing", {})
    raw_country = billing.get("country", None)
    country = normalize_country(raw_country)
    address = billing.get("address", "N/A")

    # Safely extract logo upload date
    informations = provider.get("informations", {})
    logo = informations.get("logo", {})
    logo_url = logo.get("url", "")
    logo_date = extract_logo_upload_date(logo_url)

    if name not in existing_names:
        new_providers.append([today, name, country, address, logo_date])
        country_counts[country] += 1

# === Add headers if sheet is new ===
if log_sheet.row_count == 0 or not log_sheet.row_values(1):
    log_sheet.append_row(["Date", "Name", "Country", "Address", "Logo Upload Date"])

# Append new entries
if new_providers:
    log_sheet.append_rows(new_providers)

# === 7. Update summary ===
existing_headers = summary_sheet.row_values(1)
if not existing_headers:
    existing_headers = ["Date", "Total Providers", "New Providers"]

existing_headers = update_country_headers(existing_headers, country_counts)

summary_row = [today, len(providers), len(new_providers)]
for country in existing_headers[3:]:
    summary_row.append(country_counts.get(country, 0))

summary_sheet.append_row(summary_row)

print(f"📊 Summary updated: {summary_row}")
