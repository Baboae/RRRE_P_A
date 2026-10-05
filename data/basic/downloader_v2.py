import math
import os
import json
from pathlib import Path

import requests
import typing_extensions

print("\n")

pathto_app_folder=Path(__file__).parent.parent.parent
pathto_users_folder = Path(__file__).parent.parent.joinpath("webapp").joinpath("static").joinpath("users")
itemsIn_users_folder = [u for u in os.listdir(pathto_users_folder)]


def fetch(url):
    try:
        #test a block of code
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception
        if response.status_code == 200 and "error" in response.json().keys():
            raise ValueError
    except Exception:
        #handle some sort of issue
        print("Error connecting to RaceRoom servers.")
        return response.status_code
    except ValueError:
        print("Error: user or data does not exist.")
        return 0
    else:
        #code executed if there is no error
        return response.json()
    finally:
        #code that will run regardless of the result of the test
        print(f"Response: {response}")

def download_pipeline(username):
    url_user_info = f"https://game.raceroom.com/utils/user-info/{username}"
    url_mp_rating = "https://game.raceroom.com/multiplayer-rating/user/USERID.json"
    url_career_page = "https://game.raceroom.com/users/USERNAME/career?CurrentPage=-PAGE&PageSize=100&json"
    pass

#region TESTING GROUNDS

test_good_username = f"https://game.raceroom.com/utils/user-info/Bab_0"
test_bad_username = f"https://game.raceroom.com/utils/user-info/nemletezo"

print(f"Good user-info:\n{fetch(test_good_username)}\n")
print(f"Bad user-info:\n{fetch(test_bad_username)}\n")

test_good_mp_rating = "https://game.raceroom.com/multiplayer-rating/user/6524740.json"
test_bad_mp_rating = "https://game.raceroom.com/multiplayer-rating/user/6524741.json"

print(f"Good mp-rating:\n{fetch(test_good_mp_rating)}\n")
print(f"Bad mp-rating:\n{fetch(test_bad_mp_rating)}\n")
#endregion