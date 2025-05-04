from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from sheets import connect_to_sheet, append_data
import datetime
import re
import os

app = Flask(__name__)

line_bot_api = LineBotApi('OYsBtOtimw+ksK5LTeP1BXCB7RL0oHbiVwNKAMZ6oIZ0DXfMV+4AGXVG3ITSsbNbYtP9fxX/zLrqNBe1WjgJN5wCGumzaI9WuQBcG+fkvR+0x0i34H9AsOhg71P7MZNOytSDB29BUhyTVhH0CwMh+QdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('00bf24e1a86139a305722458dd9ebcf3')

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
    reply = "請輸入健康資料，例如：體重72 體脂25 或 身高171 體重72"
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line_id = event.source.user_id
        if "體重" in msg and "體脂" in msg:
            weight = float(re.search(r"體重\s*(\d+(\.\d+)?)", msg).group(1))
            fat = float(re.search(r"體脂\s*(\d+(\.\d+)?)", msg).group(1))
            append_data(sheet, [now, line_id, "", weight, "", fat])
            reply = f"✅ 已記錄：體重 {weight}kg，體脂 {fat}%"
        elif "身高" in msg and "體重" in msg:
            height = float(re.search(r"身高\s*(\d+(\.\d+)?)", msg).group(1))
            weight = float(re.search(r"體重\s*(\d+(\.\d+)?)", msg).group(1))
            bmi = round(weight / ((height / 100) ** 2), 1)
            append_data(sheet, [now, line_id, height, weight, bmi, ""])
            reply = f"✅ 已記錄：\n身高 {height}cm\n體重 {weight}kg\nBMI：{bmi}"
    except Exception as e:
        reply = f"⚠️ 發生錯誤：{str(e)}\n請確認格式正確，例如：身高170 體重70"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
