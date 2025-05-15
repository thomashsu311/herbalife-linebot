from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os, json, datetime
from sheets import connect_to_sheet, get_or_create_worksheet, load_alias

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

sheet = connect_to_sheet(os.getenv("SHEET_NAME"))
alias_map = load_alias()

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
    uid = event.source.user_id
    profile = line_bot_api.get_profile(uid)
    name = profile.display_name
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if message_text == "選單":
        with open("flex_message_menu.json", "r", encoding="utf-8") as f:
            flex_content = json.load(f)
        flex_message = FlexSendMessage(alt_text="功能選單", contents=flex_content)
        line_bot_api.reply_message(event.reply_token, flex_message)
        return

    if message_text.startswith("註冊 "):
        tokens = message_text.split()
        if len(tokens) == 4:
            gender, height, birthday = tokens[1], tokens[2], tokens[3]
            user_ws = get_or_create_worksheet(sheet, "個人資料", ["時間", "LINE名稱", "性別", "身高", "生日"])
            user_ws.append_row([now, name, gender, height, birthday])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已完成註冊"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入：註冊 男 170 1990-01-01"))
        return

    records = {}
    for token in message_text.split():
        for key in alias_map:
            if token.startswith(key):
                value = token[len(key):]
                if value.replace(".", "").isdigit():
                    records[alias_map[key]] = value
                break

    if records:
        ws = get_or_create_worksheet(sheet, "體重記錄表", ["時間", "LINE名稱"] + list(set(alias_map.values())))
        row = [now, name]
        headers = ws.row_values(1)
        for col in headers[2:]:
            row.append(records.get(col, ""))
        ws.append_row(row)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text="✅ 已記錄：" + "、".join([f"{k} {v}" for k, v in records.items()])
        ))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text="⚠️ 找不到完整資料，請輸入例如「體重72 體脂25」或「身高171 體重72」"
        ))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)