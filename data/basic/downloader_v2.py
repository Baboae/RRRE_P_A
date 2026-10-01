import os
import json
import math
from pathlib import Path
from sys import excepthook, exception

import requests
from conda.exports import root_dir

app_folder=Path(__file__).parent.parent.parent
users_folder = Path(__file__).parent.parent.joinpath("webapp").joinpath("users")
USERFOLDERS_LIST = [u for u in os.listdir(users_folder)]

USER_INFO_URL = "https://game.raceroom.com/utils/user-info/USERNAME"
MP_RATING_URL = "https://game.raceroom.com/multiplayer-rating/user/USERID.json"
CAREER_PAGE_URL = "https://game.raceroom.com/users/USERNAME/career""?CurrentPage=-NUMOFPAGE&PageSize=100&json"

def fetch_json(URL):
    """It loads the data from the official site's server.

        If the server fails to respond, or responds with a default JSON file
        indicating that the specific file or user does not exist, it returns the status code;
        otherwise, it returns the raw data."""

    response = requests.get(URL)
    if response.status_code == 200 and "error" not in response.json().keys():
        return response.json()
    else:
        return response.status_code

def save_json(filename, file):
    with open(filename, "w") as f:
        json.dump(file, f, indent=4)

def create_user_folder(userid, username, racescompleted):
    """If a folder does not yet exist for the user, the program creates one.

        The default naming convention I tought would be working was "{userid}_{username}_{racescompleted}".
        - ID is included at the beginning to ensure the folder can be clearly distinguished from others.
        - username is included to make it easier to locate a specific user during a manual search.
        - "racescompleted" (i.e., the number of races) is part of the name so that the folder does
         not need to be opened when data needs to be updated from the server.

         However, I realized that while this may sound foolproof it doesn't seem to be working.
         Many players have underscores in their name and when checking the foldernames, I use _ to split the name to bits.

         """

    userfolder = app_folder.joinpath("data").joinpath("webapp").joinpath("users").joinpath(f"{userid}_{username}_{racescompleted}")
    if not os.path.exists(userfolder):
        os.makedirs(userfolder)
    else:
        return 0, userfolder
    return 1, userfolder

def check_and_update_local_files(username):
    # TODO: check the foldernames in the users dir. If any of them contain the username that was in the input, go on checking if they have content or not.
    for  u in USERFOLDERS_LIST:
        if username in u:
            print(f"User data found in local folders at {users_folder.joinpath(u)}")
            #TODO: Check if folder has necessary data (user_info.json, multiplayer_rating.json, CareerPages folder full with all pages.
            if os.listdir(users_folder.joinpath(u)) == ['CareerPages', 'multiplayer_rating.json', 'user_info.json']:
                #TODO: Check what the local and live mp-rating file says racecount-wise. If there is a difference, data must be refreshed.
                mp_rating_json = users_folder.joinpath(u).joinpath('multiplayer_rating.json')
                with open(mp_rating_json) as f:
                    mp_rating_local = json.load(f)
                mp_rating_live = fetch_json(MP_RATING_URL.replace("USERID", str(mp_rating_local["UserId"])))

                RacesCompleted_local = mp_rating_local['RacesCompleted']
                RacesCompleted_live = mp_rating_live['RacesCompleted']
                print(f"Races Completed, local/live: {RacesCompleted_local} / {RacesCompleted_live}")

                CareerPages_Num_local = len(os.listdir(users_folder.joinpath(u).joinpath("CareerPages")))
                CareerPages_Num_live = math.ceil(RacesCompleted_live/100)
                print(f"Career Pages, local/live: {CareerPages_Num_local}/{CareerPages_Num_live}")

                if RacesCompleted_local == RacesCompleted_live and CareerPages_Num_local != CareerPages_Num_live:
                    Pages_local = [page for page in os.listdir(users_folder.joinpath(u).joinpath("CareerPages"))]
                    for page in range(1, CareerPages_Num_live + 1):
                        if f"Page_{page}.json" not in Pages_local:

                            currentpage = CAREER_PAGE_URL.replace("USERNAME", username)
                            currentpage = CAREER_PAGE_URL.replace("NUMOFPAGE", str(page))
                            print(f"Downloading missing page #{page} from {currentpage}")
                            downloaded_raw = fetch_json(currentpage)
                            print(downloaded_raw)
                            filename=users_folder.joinpath(u).joinpath("CareerPages").joinpath(f"Page_{page}.json")
                            save_json(filename, downloaded_raw)
                            print(f"Saved at {filename}")

    return None

def start_download_pipeline(username):
    """This is what I plan to call when the user clicks search on the site. It's still WIP.

    """
    check_and_update_local_files(username)
print("\nEdge case 1: valid user with all data downloaded")
start_download_pipeline("Bab_0")

print("\nEdge case 2: valid user with missing pagefiles/races")
start_download_pipeline("Orban_k")

