from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

app = Flask(__name__)

# 讀取環境變數
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.environ.get("LINE_CHANNEL_SECRET")

print("[Init] 取得 access_token:", bool(channel_access_token))
print("[Init] 取得 secret:", bool(channel_secret))

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# Google Sheet 連線
def connect_to_sheet(sheet_name):
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(google_creds_json)
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name)

sheet_name = os.environ.get("SHEET_NAME", "賀寶芙體重管理記錄表")
try:
    sheet = connect_to_sheet(sheet_name).sheet1
    print("[Init] 成功連接 Google Sheet")
except Exception as e:
    print("[Init] Google Sheet 連線失敗:", str(e))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("[Callback] 接收到訊息：", body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("[Error] 簽名驗證失敗")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.replace("　", " ").replace("\u3000", " ").strip()
    uid = event.source.user_id
    name = "TestUser"  # 如有取 profile 可改為 display_name
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[Message] 收到：{msg}｜來自：{uid}")

    if msg.startswith("註冊"):
        print("[Logic] 進入註冊判斷")
        tokens = msg.split()
        if len(tokens) >= 4:
            gender, height, birthday = tokens[1], tokens[2], tokens[3]
            try:
                sheet.append_row([now, name, gender, height, birthday])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已完成註冊"))
                print("[Sheet] 已寫入使用者資料")
            except Exception as e:
                print("[Sheet Error]", str(e))
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 資料寫入失敗"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入：註冊 性別 身高 生日"))
        return

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 指令尚未支援或格式錯誤"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)