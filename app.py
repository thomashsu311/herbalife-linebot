
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route("/")
def index():
    return "LIFF redirect active - static test v1.0"

@app.route("/form_fresh")
def form_fresh():
    return send_from_directory("static", "form_fresh.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)
