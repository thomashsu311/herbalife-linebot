from flask import Flask, render_template, redirect

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('form.html')  # 指向更新後的表單

if __name__ == '__main__':
    app.run()
