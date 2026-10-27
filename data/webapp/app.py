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

def datetimeformat(value):
  return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
app.jinja_env.filters["datetimeformat"] = datetimeformat
@app.route('/')
def index():
    return render_template("index.html")
@app.route('/local.html')
def local():
    user_infos = []
    mp_ratings = []
    for user in os.listdir('static/users'):

        with open(os.path.join(f"static/users/{user}/user_info.json"), 'r', encoding="utf-8") as f:
            user_infos.append(json.load(f))
        with open(os.path.join(f"static/users/{user}/multiplayer_rating.json"), 'r', encoding="utf-8") as f:
            mp_ratings.append(json.load(f))

    return render_template("local.html", user_infos=user_infos, mp_ratings=mp_ratings)
@app.route('/user/<username>')
def user(username):
    pages = []
    pages_path = f"static/users/{username}/CareerPages"
    for page in os.listdir(pages_path):
        with open(os.path.join(pages_path, page), 'r', encoding="utf-8") as f:
            pages.append(json.load(f))
    return render_template("user.html", username=username, pages=pages)
if __name__ == '__main__':
    app.run(debug=True)
