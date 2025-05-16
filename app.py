from flask import Flask, render_template, redirect

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/form-liff')
def form_liff():
    return redirect('/')
