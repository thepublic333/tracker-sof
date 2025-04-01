import requests
import gspread
import os
import json
from urllib.parse import urlparse
from datetime import datetime
from google.oauth2.service_account import Credentials

# === 1. Load Google Sheets credentials ===
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

# === 2. Google Sheet setup ===
sheet = client.open("Sofwave Provider Data")
processing_sheet = sheet.worksheet("processing")

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
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://sofwave.com/",
    "Origin": "https://sofwave.com",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

response = requests.get(url, headers=headers, params=params, timeout=60)
providers = response.json().get("items", [])

# === 4. Helpers ===
def extract_logo_upload_date(logo_url):
    try:
        parts = urlparse(logo_url).path.split("/")
        year, month = parts[-3], parts[-2]
        return f"{year}-{month}"
    except:
        return "Null"

# === 5. Process + Sort Providers by ID ===
rows = []
for p in providers:
    billing = p.get("billing", {}) or {}
    contact = p.get("contact", {}) or {}
    info = p.get("informations", {}) or {}
    logo = info.get("logo", {}) or {}

    rows.append([
        p.get("id", ""),
        p.get("title", ""),
        contact.get("website", ""),
        contact.get("email", ""),
        contact.get("phone", ""),
        billing.get("address", ""),
        billing.get("country", ""),
        extract_logo_upload_date(logo.get("url", "")),
        datetime.utcnow().strftime("%Y-%m-%d")  # scrape date
    ])

rows.sort(key=lambda x: int(x[0]) if x[0] else 0)

# === 6. Write to Sheet ===
headers = [
    "ID", "Name", "Website", "Email", "Phone",
    "Address", "Country", "Logo Upload Date", "Scraped On"
]
processing_sheet.clear()
processing_sheet.append_row(headers)
processing_sheet.append_rows(rows)

print(f"✅ Wrote {len(rows)} providers to 'processing' sheet")
