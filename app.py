from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return 'LIFF demo running!'

@app.route('/form-liff')
def form_liff():
    return render_template('form_liff.html')
