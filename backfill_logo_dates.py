import gspread
from google.oauth2.service_account import Credentials
import os
import json
import requests
import time
import re

# === Load credentials ===
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

# === Sheet setup ===
sheet = client.open("Sofwave Provider Data")
log_sheet = sheet.worksheet("Log")

# === Extract logo upload date ===
def extract_logo_upload_date(logo_url: str) -> str:
    if not logo_url:
        return "Null"
    match = re.search(r"/(\d{4})/(\d{2})/", logo_url)
    if match:
        year, month = match.groups()
        return f"{year}-{month}-01"
    return "Null"

# === Fetch Sofwave API data ===
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
    "Accept": "application/json"
}

print("📡 Fetching Sofwave data...")
response = requests.get(url, headers=headers, params=params, timeout=60)
data = response.json()
providers = data.get("items", [])
print(f"✅ Retrieved {len(providers)} providers")

# === Build lookup: name → logo upload date ===
logo_date_map = {}
for p in providers:
    name = p.get("title", "")
    logo = p.get("informations", {}).get("logo")
    logo_url = logo.get("url", "") if logo else ""
    logo_date_map[name] = extract_logo_upload_date(logo_url)

# === Get headers + records ===
all_values = log_sheet.get_all_values()
headers = all_values[0]
rows = all_values[1:]

# === Add new column if not exists ===
if "Logo Upload Date" not in headers:
    headers.append("Logo Upload Date")
    log_sheet.resize(rows=len(rows) + 1, cols=len(headers))
    log_sheet.update("A1", [headers])

# === Prepare updated values ===
updated_data = []
name_index = headers.index("Name")
logo_index = headers.index("Logo Upload Date")

for row in rows:
    name = row[name_index]
    while len(row) < len(headers):  # pad if needed
        row.append("")
    if not row[logo_index]:  # only update if blank
        row[logo_index] = logo_date_map.get(name, "Null")
    updated_data.append(row)

# === Overwrite all rows with updates ===
log_sheet.update(f"A2", updated_data)
print("✅ Logo Upload Dates backfilled successfully.")
