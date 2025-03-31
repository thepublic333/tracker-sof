import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json

# Load Google Sheets credentials from GitHub Secrets
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open("Sofwave Provider Data").sheet1

# API call to Sofwave
url = "https://api.sofwave.com/wp-json/cherami/v1/provider"
params = {
    "is_resume": "true",
    "long": 65.7067,
    "lat": 0.0000,
    "bounds[sw_lat]": -85.05112899999985,
    "bounds[sw_long]": -180.08542572340858,
    "bounds[ne_lat]": 85.05112877980659,
    "bounds[ne_long]": 311.4988519149046
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://sofwave.com/",
    "Origin": "https://sofwave.com"
}

response = requests.get(url, params=params, headers=headers, timeout=60)
data = response.json()

providers = data.get("providers", [])
print(f"Got {len(providers)} providers")

provider_data = []
for provider in providers:
    name = provider.get("name", "N/A")
    location = provider.get("formatted_address", "N/A")
    provider_data.append([name, location])


# Update the Google Sheet
sheet.clear()
sheet.append_row(["Total Providers", len(provider_data)])
sheet.append_row([])
sheet.append_row(["Name", "Location"])
sheet.append_rows(provider_data)
