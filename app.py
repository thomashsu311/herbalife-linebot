from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, MessagingApi
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
import os

app = Flask(__name__)
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)
line_bot_api = MessagingApi(configuration)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return 'OK'

# 加入 Web Server 啟動必要區塊 (Render 需要)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))