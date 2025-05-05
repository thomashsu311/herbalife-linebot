from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, FlexSendMessage
import os
import re
import json
import datetime
import matplotlib.pyplot as plt
from pytz import timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("LINE_CHANNEL_SECRET"))

# ✅ Sheets 連線
def connect_to_sheet(sheet_name):
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("未設定 GOOGLE_CREDENTIALS 環境變數")
    creds_dict = json.loads(creds_json)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    return gc

gc = connect_to_sheet(os.environ.get("SHEET_NAME", "賀寶芙體重管理記錄表"))
sheet = gc.open(os.environ.get("SHEET_NAME")).sheet1
profile_sheet = None
try:
    profile_sheet = gc.open(os.environ.get("SHEET_NAME")).worksheet("使用者資料")
except:
    profile_sheet = gc.open(os.environ.get("SHEET_NAME")).add_worksheet(title="使用者資料", rows="100", cols="10")
    profile_sheet.append_row(["user_id", "display_name", "性別", "身高", "生日"])

def get_display_name(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except:
        return user_id

def draw_weight_trend(dates, weights, display_name):
    path = f"/mnt/data/{display_name}_trend.png"
    plt.figure(figsize=(8,4))
    plt.plot(dates, weights, marker="o")
    plt.title(f"{display_name} 體重趨勢圖（最近{len(dates)}筆）")
    plt.xlabel("日期")
    plt.ylabel("體重（kg）")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path

def get_recent_weights(sheet, display_name, N=7):
    rows = sheet.get_all_values()[1:]
    filtered = [r for r in rows if r[1] == display_name and r[3]]
    recent = filtered[-N:]
    dates = [r[0] for r in recent]
    weights = [float(r[3]) for r in recent]
    return dates, weights

def find_user_profile(user_id):
    data = profile_sheet.get_all_values()
    for row in data[1:]:
        if row[0] == user_id:
            return {
                "user_id": row[0],
                "display_name": row[1],
                "gender": row[2],
                "height": row[3],
                "birthday": row[4]
            }
    return None

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
    uid = event.source.user_id
    name = get_display_name(uid)
    tz = timezone("Asia/Taipei")
    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    # ✅ 註冊個人資料
    if msg.startswith("註冊"):
        tokens = msg.split()
        if len(tokens) >= 4:
            gender, height, birthday = tokens[1], tokens[2], tokens[3]
            profile_sheet.append_row([uid, name, gender, height, birthday])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 個人資料已登錄！"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入：註冊 性別 身高 生日（例如：註冊 男 171 1980-01-01）"))
        return

    # ✅ 查詢個人資料
    if "個人資料" in msg:
        profile = find_user_profile(uid)
        if profile:
            flex = {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://i.imgur.com/ijQ3zZq.png",
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": profile["display_name"], "weight": "bold", "size": "xl"},
                        {"type": "text", "text": f"性別：{profile['gender']}"},
                        {"type": "text", "text": f"身高：{profile['height']} cm"},
                        {"type": "text", "text": f"生日：{profile['birthday']}"}
                    ]
                }
            }
            line_bot_api.reply_message(event.reply_token, FlexSendMessage("個人資料卡", flex))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="尚未註冊，請輸入：註冊 性別 身高 生日"))
        return

    # ✅ 折線圖
    if "趨勢圖" in msg or "體重趨勢" in msg:
        dates, weights = get_recent_weights(sheet, name, 7)
        if dates:
            img_path = draw_weight_trend(dates, weights, name)
            url = os.environ.get("STATIC_IMAGE_BASE_URL", "") + "/" + os.path.basename(img_path)
            img = ImageSendMessage(original_content_url=url, preview_image_url=url)
            line_bot_api.reply_message(event.reply_token, img)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到趨勢資料"))
        return

    if "上傳照片" in msg:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📷 請傳一張照片進行上傳記錄！"))
        return

    # ✅ 體重紀錄與 BMI
    weight = re.search(r"體重[:：]?\s*(\d+(?:\.\d+)?)", msg)
    fat = re.search(r"體脂[:：]?\s*(\d+(?:\.\d+)?)", msg)
    height = re.search(r"身高[:：]?\s*(\d+(?:\.\d+)?)", msg)

    try:
        if height and weight:
            h = float(height.group(1))
            w = float(weight.group(1))
            bmi = round(w / ((h / 100)**2), 1)
            sheet.append_row([now, name, h, w, bmi, ""])
            reply = f"✅ 已記錄：身高 {h}cm 體重 {w}kg
BMI：{bmi}"
        elif weight and fat:
            w = float(weight.group(1))
            f = float(fat.group(1))
            sheet.append_row([now, name, "", w, "", f])
            reply = f"✅ 已記錄：體重 {w}kg 體脂 {f}%"
        else:
            reply = "⚠️ 請輸入：體重80 體脂25 或 身高171 體重80"
    except Exception as e:
        reply = f"⚠️ 錯誤：{str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
