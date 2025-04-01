import requests
import gspread
import os
import json
import time
from datetime import datetime
from google.oauth2.service_account import Credentials

# === 1. Google Sheets Auth ===
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

# === 2. Sheet Handles ===
sheet = client.open("Sofwave Provider Data")
korea_sheet = sheet.worksheet("Korea")

# === 3. Setup ===
BASE_URL = "https://sofwave.co.kr/itboard/front/board/hospital/list.ajax.php"
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://sofwave.co.kr',
    'Referer': 'https://sofwave.co.kr/hospital/',
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest'
}
COOKIES = {
    'sofwave': 'sofwave'
}

# === 4. Helpers ===
def fetch_page(page):
    payload = {
        "page": page,
        "limit": 5,
        "sh": "",
        "sido": "",
        "gugun": ""
    }
    res = requests.post(BASE_URL, headers=HEADERS, data=payload, cookies=COOKIES, timeout=15, verify=False)
    res.raise_for_status()
    return res.json()

def get_all_hospitals():
    all_data = []
    first_page = fetch_page(1)
    total = first_page['TOTAL']
    total_pages = (total + 4) // 5

    all_data.extend(first_page['LIST'])

    for page in range(2, total_pages + 1):
        time.sleep(0.5)
        result = fetch_page(page)
        all_data.extend(result['LIST'])

    return all_data

def get_existing_ids():
    try:
        rows = korea_sheet.get_all_records()
        return set(row['id'] for row in rows)
    except Exception:
        return set()

# === 5. Run ===
print("🔍 Scraping Korean hospital data...")
hospitals = get_all_hospitals()
existing_ids = get_existing_ids()
new_rows = []

today = datetime.now().strftime("%Y-%m-%d")

for h in hospitals:
    hospital_id = h.get('board_id', '')
    if hospital_id not in existing_ids:
        name = h.get('title', '')
        address = h.get('addr1', '') + (', ' + h.get('addr2', '') if h.get('addr2', '') else '')
        phone = h.get('phone', '')
        region = f"{h.get('sido', '')} {h.get('gugun', '')}"
        reg_date = h.get('first_reg_date', '')
        lat = h.get('ylang', '')
        lon = h.get('xlang', '')
        new_rows.append([today, hospital_id, name, region, address, phone, lat, lon, reg_date])

# === 6. Append ===
if new_rows:
    korea_sheet.append_rows(new_rows)
    print(f"✅ Appended {len(new_rows)} new hospitals to 'Korea'")
else:
    print("📭 No new hospitals found.")

