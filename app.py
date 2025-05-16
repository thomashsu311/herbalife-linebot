
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

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Timezone for Taiwan
tz = timezone(timedelta(hours=8))

def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(os.getenv("GOOGLE_SHEET_KEY"))
    return spreadsheet

@app.route("/")
def hello():
    return "Hello from Line Bot!"

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
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠ 請輸入格式：註冊 男 171 1969-03-11"))
    else:
        try:
            data = parse_text(user_text)
            if data:
                now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                sheet = get_gsheet().worksheet("體重紀錄")
                sheet.append_row([now, display_name] + data)
                text = f"✅ 已記錄：體重 {data[0]}, 體脂率 {data[1]}, 內臟脂 {data[2]}"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠ 格式錯誤，請輸入如：體重95.3 體脂30.8 內脂14"))
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠ 發生錯誤：" + str(e)))

def parse_text(text):
    weight = bodyfat = visceral = None
    for part in text.split():
        if part.startswith("體重"):
            weight = float(part.replace("體重", ""))
        elif part.startswith("體脂"):
            bodyfat = float(part.replace("體脂", ""))
        elif part.startswith("內脂") or part.startswith("內臟"):
            visceral = float(part.replace("內脂", "").replace("內臟", ""))
    if weight and bodyfat and visceral is not None:
        return [weight, bodyfat, visceral]
    return None

if __name__ == "__main__":
    app.run()
