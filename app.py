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
    sheet = gc.open(sheet_name).sheet1
    return sheet

sheet = connect_to_sheet(os.environ.get("SHEET_NAME", "賀寶芙體重管理記錄表"))

# ✅ 顯示名稱
def get_display_name(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except:
        return user_id

# ✅ 畫圖
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

# ✅ 查詢資料
def get_recent_weights(sheet, display_name, N=7):
    rows = sheet.get_all_values()[1:]
    filtered = [r for r in rows if r[1] == display_name and r[3]]
    recent = filtered[-N:]
    dates = [r[0] for r in recent]
    weights = [float(r[3]) for r in recent]
    return dates, weights

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
    msg = event.message.text.strip().replace("　", "").replace(" ", "")
    uid = event.source.user_id
    name = get_display_name(uid)
    tz = timezone("Asia/Taipei")
    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    # ✅ 指令：個人資料
    if "個人資料" in msg:
        reply = f"👤 {name} 的基本資料尚未建置。
敬請期待表單功能！"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # ✅ 指令：折線圖
    if "趨勢圖" in msg or "體重趨勢" in msg:
        dates, weights = get_recent_weights(sheet, name, 7)
        if dates:
            img_path = draw_weight_trend(dates, weights, name)
            url = os.environ.get("STATIC_IMAGE_BASE_URL", "") + "/" + os.path.basename(img_path)
            image_message = ImageSendMessage(original_content_url=url, preview_image_url=url)
            line_bot_api.reply_message(event.reply_token, image_message)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到趨勢資料"))
        return

    # ✅ 指令：上傳照片
    if "上傳照片" in msg:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📷 請傳一張照片進行上傳記錄！"))
        return

    # ✅ 處理體重+體脂 / BMI 計算
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
            reply = "⚠️ 找不到完整資料，請輸入如「體重72 體脂25」或「身高171 體重72」"
    except Exception as e:
        reply = f"⚠️ 錯誤：{str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
