from flask import Flask, render_template, request
from data.basic import downloader
from data.basic.performance_analyzer_functions import *
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATES_DIR)
print(BASE_DIR)
print(TEMPLATES_DIR)
@app.route('/')
def index():
    return render_template("index.html")
@app.route('/local.html')
def local():
    users = []
    for user in os.listdir('static/users'):
        with open(os.path.join(f"static/users/{user}/multiplayer_rating.json"), 'r', encoding="utf-8") as f:
            users.append(json.load(f))
    return render_template("local.html", users=users)

if __name__ == '__main__':
    app.run(debug=True)
