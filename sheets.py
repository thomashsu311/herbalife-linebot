import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def connect_to_sheet(sheet_name):
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not google_creds_json:
        raise ValueError("未設定 GOOGLE_CREDENTIALS 環境變數")
    creds_dict = json.loads(google_creds_json)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def append_data(sheet, data):
    if len(data) != 6:
        raise ValueError("資料欄位數不正確，應為 6 項")
    sheet.append_row(data)
