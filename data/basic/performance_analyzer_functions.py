import os
import json
from pathlib import Path
from data.basic.model import *
from data.basic.downloader import download_career_pages, BASE_DIR

BASE_DIR = Path(__file__).resolve().parent.parent.parent

users_dir = BASE_DIR / "users"

def podium_stats(user_folder):
    career_pages_folder = os.path.join(user_folder, 'CareerPages')
    career_pages_filenames = [f for f in os.listdir(career_pages_folder) if f.endswith(".json")]

    first = []
    second = []
    third = []

    for filename in career_pages_filenames:
        with open(os.path.join(career_pages_folder, filename), 'r') as f:
            data = json.load(f)
            races = data["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["Entries"]
            for race in races:
                if race["FinishPosition"] == 1:
                    first.append(race["RaceHash"])
                if race["FinishPosition"] == 2:
                    second.append(race["RaceHash"])
                if race["FinishPosition"] == 3:
                    third.append(race["RaceHash"])
    return [len(first), len(second), len(third)]

def basic_user_information(user_folder):
    with open(os.path.join(user_folder, 'user_info.json'), 'r') as user_info:
        a = json.load(user_info)
        team = a["team"]
        if team == "":
            team = "privateer"
    with open(os.path.join(user_folder, 'multiplayer_rating.json'), 'r') as user_mp_info:
        b = json.load(user_mp_info)
    return Player(a["id"], a["username"], a["name"], team, a["country"], b["Rating"], b["Reputation"], b["RacesCompleted"], b["Position"])

#print(basic_user_information(users_dir / "Bab_0_6524740"))