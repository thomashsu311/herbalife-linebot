
from flask import Flask, request, abort
from linebot.v3.messaging import Configuration, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.models import ReplyMessageRequest, TextMessage
import os
from sheets import handle_user_input, ensure_user_registered, update_user_profile

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
msg_api = MessagingApi(configuration=config)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text.strip()
    display_name = get_display_name(user_id)

    # 註冊指令解析
    if user_message.startswith("註冊"):
        params = user_message.replace("註冊", "").strip().split()
        profile_data = {}
        for param in params:
            if param.startswith("性別"):
                profile_data["gender"] = param.replace("性別", "")
            elif param.startswith("身高"):
                profile_data["height"] = param.replace("身高", "")
            elif param.startswith("生日"):
                profile_data["birthday"] = param.replace("生日", "")
            elif param.startswith("教練"):
                profile_data["coach"] = param.replace("教練", "")
        update_user_profile(
            user_id,
            display_name,
            gender=profile_data.get("gender"),
            height=profile_data.get("height"),
            birthday=profile_data.get("birthday"),
            coach=profile_data.get("coach")
        )
        reply = "✅ 註冊成功！已更新："
        for k, v in profile_data.items():
            reply += f"\n{k.replace('gender','性別').replace('height','身高').replace('birthday','生日').replace('coach','教練')}：{v}"
        send_text(event.reply_token, reply)
    else:
        reply = handle_user_input(user_id, display_name, user_message)
        send_text(event.reply_token, reply)

def send_text(token, text):
    msg = TextMessage(text=text)
    body = ReplyMessageRequest(reply_token=token, messages=[msg])
    msg_api.reply_message_with_http_info(body)

def get_display_name(user_id):
    # 模擬用（開發階段可寫死或回傳 user_id）
    return "許志豪"

if __name__ == "__main__":
    app.run()
