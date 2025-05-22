
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
import os
import json
import base64

# 讀取 service account 憑證
creds_json = base64.b64decode(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")).decode()
creds_dict = json.loads(creds_json)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

# 連接 Google Sheet
gc = gspread.authorize(creds)
sheet = gc.open_by_key(os.getenv("GOOGLE_SHEET_ID"))
user_sheet = sheet.worksheet("個人資料")

def update_user_profile(user_id, display_name, gender=None, height=None, birthday=None, coach=None):
    now = datetime.now().strftime("%Y-%m-%d")
    headers = user_sheet.row_values(1)
    records = user_sheet.get_all_records()

    row_index = None
    for i, row in enumerate(records, start=2):
        if str(row.get("LINE ID")) == user_id:
            row_index = i
            break

    data_to_update = {
        "時間": now,
        "LINE ID": user_id,
        "LINE名稱": display_name,
        "性別": gender,
        "身高": height,
        "生日": birthday,
        "教練": coach
    }

    # 將 None 過濾掉，只更新有值的欄位
    data_to_update = {k: v for k, v in data_to_update.items() if v is not None}

    if row_index:  # 如果已存在，進行更新
        for key, value in data_to_update.items():
            if key in headers:
                col = headers.index(key) + 1
                user_sheet.update_cell(row_index, col, value)
    else:  # 如果不存在，新增一筆
        new_row = [data_to_update.get(h, "") for h in headers]
        user_sheet.append_row(new_row)
