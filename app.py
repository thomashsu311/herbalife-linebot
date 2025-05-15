from flask import Flask, request, render_template_string
import os
import json
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

def connect_to_sheet(sheet_name):
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name)

sheet_name = os.getenv("SHEET_NAME", "賀寶芙體重管理記錄表")
sheet = connect_to_sheet(sheet_name)
ws = sheet.worksheet("體重記錄表")

@app.route("/")
def form():
    return render_template_string(open("templates/form.html", encoding="utf-8").read())

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    height = request.form.get("height")
    weight = request.form.get("weight")
    fat = request.form.get("fat")
    visceral = request.form.get("visceral")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [now, name, height, weight, fat, visceral]
    ws.append_row(row)
    return "✅ 已成功記錄！可以關閉此頁面或返回填寫更多資料。"

if __name__ == "__main__":
    app.run(debug=True, port=5000)