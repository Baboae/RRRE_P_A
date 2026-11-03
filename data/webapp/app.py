from asyncio import windows_utils

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
  return datetime.fromtimestamp(value).strftime("%Y-%m-%d")
app.jinja_env.filters["datetimeformat"] = datetimeformat


def collect_cached_users():
    """Returns 3 list (2nd n 3rd is JSON):
    1st: list of all users
    2nd: raw user-info of the corresponding user
    3rd: raw multiplayer-rating of the corresponding user"""
    users = []
    user_infos = []
    mp_ratings = []
    for user in os.listdir('static/users'):
        users.append(user)
        with open(os.path.join(f"static/users/{user}/user_info.json"), 'r', encoding="utf-8") as f:
            user_infos.append(json.load(f))
        with open(os.path.join(f"static/users/{user}/multiplayer_rating.json"), 'r', encoding="utf-8") as f:
            mp_ratings.append(json.load(f))
    return users, user_infos, mp_ratings

def alltime_podiums(username):
    seen_hashes = []
    podiums = [0,0,0]
    for page in os.listdir(f"static/users/{username}/CareerPages"):
        with open(f"static/users/{username}/CareerPages/{page}", "r", encoding="utf-8") as f:
            currentpage = json.load(f)
            for line in currentpage['context']['c']['raceList']['GetUserMpRatingProgressResult']['Entries']:
                if line['RaceHash'] not in seen_hashes:
                    if line['FinishPosition'] == 1:
                        podiums[0] += 1
                    if line['FinishPosition'] == 2:
                        podiums[1] += 1
                    if line['FinishPosition'] == 3:
                        podiums[2] += 1
                    seen_hashes.append(line['RaceHash'])
    print(len(seen_hashes))
    return podiums

def round_to_three_dec(number):
    return round(number,3)
app.jinja_env.filters["round_to_three_dec"] = round_to_three_dec
@app.route('/')
def index():
    chached = collect_cached_users()
    users, user_infos ,mp_ratings = chached[0], chached[1], chached[2]
    return render_template("index.html", users=users, user_infos=user_infos, multiplayer_ratings=mp_ratings)
@app.route('/user/<username>')
def user(username):

    alltime_podiums(username)

    user_info = ""
    multiplayer_rating = ""

    with open(os.path.join(f"static/users/{username}/user_info.json"), 'r', encoding="utf-8") as f:
        user_info = json.load(f)
    with open (os.path.join(f"static/users/{username}/multiplayer_rating.json"), 'r', encoding="utf-8") as f:
        multiplayer_rating = json.load(f)

    pages = []
    pages_path = f"static/users/{username}/CareerPages"
    for page in os.listdir(pages_path):
        with open(os.path.join(pages_path, page), 'r', encoding="utf-8") as f:
            pages.append(json.load(f))
    return render_template("user.html",
                           username=username, pages=pages, user_info=user_info,
                           multiplayer_rating=multiplayer_rating, alltime_podiums=alltime_podiums(username))
if __name__ == '__main__':
    app.run(debug=True)
