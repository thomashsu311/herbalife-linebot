from flask import Flask, render_template, redirect

app = Flask(__name__)

@app.route('/')
def index():
    return redirect('/form-liff')

@app.route('/form-liff')
def form_liff():
    return render_template('form_liff.html')
