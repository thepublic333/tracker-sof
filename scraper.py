import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import time

# === 1. Load Google Sheets credentials ===
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open("Sofwave Provider Data").sheet1

# === 2. Wait before sending request (optional mimic human) ===
time.sleep(3)

# === 3. API Call ===
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

# === 4. Extract provider info ===
provider_data = []
for provider in providers:
    name = provider.get("title", "N/A")
    billing = provider.get("billing", {})
    location = billing.get("address", "N/A")
    provider_data.append([name, location])

# === 5. Push to Google Sheets ===
sheet.clear()
sheet.append_row(["Total Providers", len(provider_data)])
sheet.append_row([])
sheet.append_row(["Name", "Location"])
sheet.append_rows(provider_data)
