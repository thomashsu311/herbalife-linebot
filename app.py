from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from sheets import connect_to_sheet, append_data
import datetime
import pytz
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Channel Access Token 與 Secret（實際填入）
line_bot_api = LineBotApi('OYsBtOtimw+ksK5LTeP1BXCB7RL0oHbiVwNKAMZ6oIZ0DXfMV+4AGXVG3ITSsbNbYtP9fxX/zLrqNBe1WjgJN5wCGumzaI9WuQBcG+fkvR+0x0i34H9AsOhg71P7MZNOytSDB29BUhyTVhH0CwMh+QdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('00bf24e1a86139a305722458dd9ebcf3')

# 連接 Google Sheet
sheet = connect_to_sheet('賀寶芙體重管理記錄表')

# 欄位順序（對應 Google Sheet）
columns = [
    "日期", "LINE名稱", "稱呼", "身高", "體重", "BMI", "體脂率", "體水份量", "脂肪量",
    "心率", "蛋白質量", "肌肉量", "肌肉率", "身體水份", "蛋白質率", "骨鹽率", "骨骼肌量",
    "內臟脂肪", "基礎代謝率", "身體年齡"
]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info(f"[Webhook] Received body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("[Webhook] ❌ Invalid signature")
        return 'Invalid signature', 400
    except Exception as e:
        app.logger.error(f"[Webhook] ❌ Unexpected error: {e}")
        return 'Error', 500

    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    if "體重" in msg and "體脂" in msg:
        try:
            user_id = event.source.user_id
            profile = line_bot_api.get_profile(user_id)
            display_name = profile.display_name

            tz = pytz.timezone('Asia/Taipei')
            now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            alias = {
                "體脂": "體脂率",
                "肌肉": "肌肉量",
                "內脂": "內臟脂肪",
                "年齡": "身體年齡",
                "稱": "稱呼"
            }

            data = {
                "日期": now,
                "LINE名稱": display_name
            }

            for key in columns[2:]:
                targets = [key] + [k for k, v in alias.items() if v == key]
                for target in targets:
                    if target in msg:
                        try:
                            value = msg.split(target)[1].split(" ")[0]
                            value = value.replace("kg", "").replace("%", "")
                            data[key] = value
                        except:
                            continue

            row = [data.get(col, "") for col in columns]
            append_data(sheet, row)

            reply = f"✅ 已記錄：體重 {data.get('體重', '?')}kg，體脂 {data.get('體脂率', '?')}%"
        except Exception as e:
            app.logger.error(f"[Parser] ❌ Error: {e}")
            reply = "⚠️ 發生錯誤，請確認格式，例如：體重72 體脂25"
    else:
        reply = "請輸入健康資料，例如：體重72 體脂25"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
