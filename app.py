from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
tz = timezone(timedelta(hours=8))

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 載入 alias.json
with open("alias.json", "r", encoding="utf-8") as f:
    alias_map = json.load(f)

# 定義正確欄位順序
official_columns = [
    "日期", "LINE名稱", "稱呼", "身高", "體重", "BMI", "體脂率", "體水份量", "脂肪量",
    "心率", "蛋白質量", "肌肉量", "肌肉率", "身體水份", "蛋白質率", "骨鹽率",
    "骨骼肌量", "內臟脂肪", "基礎代謝率", "身體年齡"
]

def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(os.getenv("GOOGLE_SHEET_KEY"))
    return spreadsheet

@app.route("/")
def home():
    return "Herbalife LineBot is running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()
    profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name

    if user_text.startswith("註冊"):
        try:
            _, gender, height, birthday = user_text.split()
            sheet = get_gsheet().worksheet("使用者資料")
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([now, display_name, gender, height, birthday])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已完成註冊"))
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠ 註冊格式錯誤：" + str(e)))
        return

    try:
        data_dict = parse_text(user_text)
        if data_dict:
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            row = [now, display_name]
            for col in official_columns[2:]:
                row.append(data_dict.get(col, ""))
            sheet = get_gsheet().worksheet("體重記錄表")
            sheet.append_row(row)
            reply = f"✅ 已記錄：" + ", ".join(f"{k} {v}" for k, v in data_dict.items())
        else:
            reply = "⚠ 格式錯誤，請輸入如：體重95.3 體脂30.8 內脂14"
    except Exception as e:
        reply = "⚠ 發生錯誤：" + str(e)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

def parse_text(text):
    data = {}
    for part in text.split():
        for alias, key in alias_map.items():
            if part.startswith(alias):
                try:
                    value = part.replace(alias, "")
                    value = float(value) if "." in value else int(value)
                    data[key] = value
                except:
                    data[key] = ""
    return data if data else None

if __name__ == "__main__":
    app.run()
