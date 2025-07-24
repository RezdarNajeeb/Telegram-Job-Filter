import os
import gspread
from google.oauth2.service_account import Credentials

def log_to_sheet(messages):
    if not messages:
        return

    sheet_id = os.getenv("SHEET_ID")
    creds_path = os.getenv("SHEET_CREDENTIALS")
    creds = Credentials.from_service_account_file(creds_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1

    rows = [[m["date"], m["channel"], m["text"]] for m in messages]
    sheet.append_rows(rows)
    print(f"📊 Logged {len(messages)} messages to Google Sheet")
