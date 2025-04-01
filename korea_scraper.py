import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime
import time


# === Google Sheets Setup ===
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

client = gspread.authorize(creds)
sheet = client.open("Sofwave Provider Data")
korea_sheet = sheet.worksheet("Korea")

# === Request Setup ===
BASE_URL = "https://sofwave.co.kr/itboard/front/board/hospital/list.ajax.php"
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://sofwave.co.kr',
    'Referer': 'https://sofwave.co.kr/hospital/',
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest'
}
COOKIES = {'sofwave': 'sofwave'}

def fetch_page(page: int):
    data = {
        'page': page,
        'limit': 5,
        'sh': '',
        'sido': '',
        'gugun': ''
    }
    res = requests.post(BASE_URL, headers=HEADERS, data=data, cookies=COOKIES, verify=False)
    return res.json()

def fetch_all_hospitals():
    first_page = fetch_page(1)
    total = first_page['TOTAL']
    total_pages = (total + 4) // 5
    all_data = first_page['LIST']
    for page in range(2, total_pages + 1):
        response = fetch_page(page)
        all_data.extend(response['LIST'])
    return all_data

def ensure_headers():
    headers = korea_sheet.row_values(1)
    expected = ["Name", "City", "Registration Date", "Scraped Date"]
    if headers != expected:
        korea_sheet.clear()
        korea_sheet.append_row(expected)

def update_korea_sheet():
    hospitals = fetch_all_hospitals()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    existing = korea_sheet.get_all_values()
    existing_names = {row[0] for row in existing[1:]}  # skip header
    new_rows = []

    for h in hospitals:
        name = h.get("title", "").strip()
        city = f"{h.get('sido', '').strip()} {h.get('gugun', '').strip()}"
        reg_date = h.get("first_reg_date", "").strip()
        if name and name not in existing_names:
            new_rows.append([name, city, reg_date, today])

    if new_rows:
        korea_sheet.append_rows(new_rows)

# Run script
ensure_headers()
update_korea_sheet()
