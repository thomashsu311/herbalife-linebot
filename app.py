from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os, json
from sheets import write_health_data, write_user_profile

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

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
    message_text = event.message.text.strip()
    user_id = event.source.user_id
    profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name

    # ✅ 選單指令處理
    if message_text == "選單":
        with open("flex_message_menu.json", "r", encoding="utf-8") as f:
            flex_content = json.load(f)
        flex_message = FlexSendMessage(alt_text="功能選單", contents=flex_content)
        line_bot_api.reply_message(event.reply_token, flex_message)
        return

    # ✅ 健康資料記錄處理（簡化版）
    if "體重" in message_text:
        response = write_health_data(message_text, display_name)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
        return

    # ✅ 個人資料註冊處理（格式：註冊 男 170 1990-01-01）
    if message_text.startswith("註冊 "):
        response = write_user_profile(message_text, display_name)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))
        return

    # 其他未處理文字
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入健康資料或功能指令"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)