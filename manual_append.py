import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

columns = [
    "日期", "LINE名稱", "稱呼", "身高", "體重", "BMI", "體脂率", "體水份量", "脂肪量",
    "心率", "蛋白質量", "肌肉量", "肌肉率", "身體水份", "蛋白質率", "骨鹽率", "骨骼肌量",
    "內臟脂肪", "基礎代謝率", "身體年齡"
]

data = {
    "日期": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "LINE名稱": "許志豪",
    "稱呼": "",
    "身高": "171",
    "體重": "95.1",
    "BMI": "",
    "體脂率": "30.9",
    "體水份量": "",
    "脂肪量": "",
    "心率": "",
    "蛋白質量": "",
    "肌肉量": "62.1",
    "肌肉率": "",
    "身體水份": "",
    "蛋白質率": "",
    "骨鹽率": "",
    "骨骼肌量": "",
    "內臟脂肪": "",
    "基礎代謝率": "",
    "身體年齡": "54"
}

row = [data.get(col, "") for col in columns]

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("herbalife-coach-ff0a10ab02c1.json", scope)
client = gspread.authorize(creds)
sheet = client.open("賀寶芙體重管理記錄表").sheet1
sheet.append_row(row)

print("✅ 已成功寫入 Google Sheet！")
