from playwright.sync_api import sync_playwright
import gspread
from google.oauth2.service_account import Credentials
import json
import os

# Load Google Sheets credentials from environment variable
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = ["https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open("Sofwave Provider Data").sheet1


# Scraping with Playwright
provider_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Load the provider page
    page.goto("https://sofwave.com/find-a-provider", timeout=60000)
    page.wait_for_selector('li._7duKOn')

    # Get all provider elements
    providers = page.query_selector_all('li._7duKOn')

    for provider in providers:
        name_elem = provider.query_selector('span.SSM3JD')
        address_elem = provider.query_selector('div.Ko5cpW')

        name = name_elem.inner_text().strip() if name_elem else 'N/A'
        address = address_elem.inner_text().strip() if address_elem else 'N/A'

        provider_data.append([name, address])

    browser.close()

# Update Google Sheet
sheet.clear()
sheet.append_row(["Total Providers", len(provider_data)])
sheet.append_row([])
sheet.append_row(["Name", "Location"])
sheet.append_rows(provider_data)
