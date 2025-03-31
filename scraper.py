import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json

# === 1. Load Google Sheets credentials from GitHub secret ===
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open("Sofwave Provider Data").sheet1

# === 2. API call to Sofwave ===
url = "https://api.sofwave.com/wp-json/cherami/v1/provider"
params = {
    "is_resume": "true",
    "long": 65.7067,
    "lat": 0.0000,
    "bounds[sw_lat]": -85.05112900000003,
    "bounds[sw_long]": -180.08542572340858,
    "bounds[ne_lat]": 85.05112877980659,
    "bounds[ne_long]": 311.4988519149046
}

headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://sofwave.com",
    "Priority": "u=1, i",
    "Referer": "https://sofwave.com/",
    "Sec-CH-UA": '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
}

response = requests.get(url, headers=headers, params=params, timeout=60)

if response.status_code != 200:
    raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

data = response.json()
providers = data.get("providers", [])
print(f"✅ Got {len(providers)} providers")

# === 3. Extract and write to Google Sheet ===
provider_data = []
for provider in providers:
    name = provider.get("name", "N/A")
    location = provider.get("formatted_address", "N/A")
    provider_data.append([name, location])

# Overwrite sheet content
sheet.clear()
sheet.append_row(["Total Providers", len(provider_data)])
sheet.append_row([])
sheet.append_row(["Name", "Location"])
sheet.append_rows(provider_data)
