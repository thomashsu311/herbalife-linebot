from flask import Flask, redirect

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return redirect('/static/form_fresh.html')
