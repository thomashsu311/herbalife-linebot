import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def connect_to_sheet(sheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # 從環境變數讀取 JSON 字串並解析
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    credentials_dict = json.loads(credentials_json)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def append_data(sheet, row_data):
    sheet.append_row(row_data)
