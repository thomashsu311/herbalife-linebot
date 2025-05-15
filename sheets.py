import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheet(sheet_name):
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name)

def get_or_create_worksheet(sheet, name, headers=[]):
    try:
        ws = sheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=name, rows="1000", cols="30")
        if headers:
            ws.append_row(headers)
    return ws

def load_alias():
    with open("alias.json", encoding="utf-8") as f:
        return json.load(f)