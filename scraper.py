
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

# Load Google Sheets credentials from environment variable
creds_json = os.getenv('GDRIVE_CREDENTIALS')
creds_dict = json.loads(creds_json)

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open("Sofwave Provider Data").sheet1

# Web scraping
url = "https://sofwave.com/find-a-provider"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Initialize lists to store provider data
provider_data = []

# Find all provider elements
providers = soup.find_all('li', class_='_7duKOn')

# Extract data from each provider
for provider in providers:
    try:
        name = provider.find('span', class_='SSM3JD').text.strip()
        address = provider.find('div', class_='Ko5cpW').text.strip()
        provider_id = provider['data-id']
        provider_data.append([name, address, provider_id])
    except AttributeError:
        continue

# Update the sheet
# Clear previous sheet content
sheet.clear()

# Insert total count at the top
sheet.append_row(["Total Providers", len(provider_data)])

# Leave one empty row, then set headers
sheet.append_row([])
sheet.append_row(["Name", "Location"])

# Append each provider as a separate row
sheet.append_rows(provider_data)
