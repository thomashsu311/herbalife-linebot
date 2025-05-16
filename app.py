from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from datetime import datetime
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# LINE credentials
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)
sheet_url = os.getenv("SHEET_URL")
sh = gc.open_by_url(sheet_url)
record_ws = sh.worksheet("體重紀錄")
user_ws = sh.worksheet("使用者資料")

@app.route("/")
def index():
    return "LINE Bot is running!"

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
    profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name

    text = event.message.text.strip()

    if text.startswith("註冊"):
        parts = text.split()
        if len(parts) == 4:
            gender = parts[1]
            height = parts[2]
            birth = parts[3]
            tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            user_ws.append_row([now, display_name, gender, height, birth])
            reply = f"✅ 已完成註冊"
        else:
            reply = "請輸入：註冊 性別 身高 生日（例：註冊 男 170 1980-01-01）"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 體重紀錄輸入（範例：體重95.3 體脂30.8 內脂14）
    if "體重" in text:
        weight = bodyfat = visceral = ""
        if "體重" in text:
            weight = text.split("體重")[1].split()[0]
        if "體脂" in text:
            bodyfat = text.split("體脂")[1].split()[0]
        if "內脂" in text:
            visceral = text.split("內脂")[1].split()[0]

        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        record_ws.append_row([now, display_name, weight, bodyfat, visceral])
        reply = f"✅ 已記錄：體重 {weight}, 體脂率 {bodyfat}, 內臟脂肪 {visceral}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

if __name__ == "__main__":
    app.run()
