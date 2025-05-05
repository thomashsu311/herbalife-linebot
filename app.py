from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from sheets import connect_to_sheet, append_data
import datetime

app = Flask(__name__)

# 改成你自己的 Channel access token 與 secret
line_bot_api = LineBotApi('OYsBtOtimw+ksK5LTeP1BXCB7RL0oHbiVwNKAMZ6oIZ0DXfMV+4AGXVG3ITSsbNbYtP9fxX/zLrqNBe1WjgJN5wCGumzaI9WuQBcG+fkvR+0x0i34H9AsOhg71P7MZNOytSDB29BUhyTVhH0CwMh+QdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('00bf24e1a86139a305722458dd9ebcf3')

# 改成你自己建立的 Google Sheet 名稱
sheet = connect_to_sheet('賀寶芙體重管理記錄表')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    if msg.startswith("體重") and "體脂" in msg:
        try:
            weight = msg.split("體重")[1].split(" ")[0]
            fat = msg.split("體脂")[1]
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line_id = event.source.user_id
            append_data(sheet, [now, line_id, weight, fat])
            reply = f"✅ 已記錄：體重 {weight}kg，體脂 {fat}%"
        except:
            reply = "⚠️ 請輸入正確格式，例如：體重72 體脂25"
    else:
        reply = "請輸入健康資料，例如：體重72 體脂25"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=5000)
