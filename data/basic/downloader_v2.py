import math
import os
import json
from encodings import utf_8
from pathlib import Path

import requests

app_folder=Path(__file__).parent.parent.parent
users_folder = Path(__file__).parent.parent.joinpath("webapp").joinpath("static").joinpath("users")
USERFOLDERS_LIST = [u for u in os.listdir(users_folder)]

USER_INFO_URL = "https://game.raceroom.com/utils/user-info/USERNAME"
MP_RATING_URL = "https://game.raceroom.com/multiplayer-rating/user/USERID.json"
CAREER_PAGE_URL = "https://game.raceroom.com/users/USERNAME/career?CurrentPage=-PAGE&PageSize=100&json"

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
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(file, f, indent=4, ensure_ascii=False)

def create_user_folder(userid):
    """If a folder does not yet exist for the user, the program creates one.

        If there was no folder before, it creates it, then returns 1 and the folder path.
        If there is already a folder, it returns a 0 and the folder path.
        The default naming convention for now is userid."""

    userfolder = app_folder.joinpath("data").joinpath("webapp").joinpath("static").joinpath("users").joinpath(f"{userid}")
    if not os.path.exists(userfolder):
        os.makedirs(userfolder)
        return 1, userfolder
    else:
        return 0, userfolder


def start_download_pipeline(username):
    """This is what I plan to call when the user clicks search on the site. It's still WIP."""
    user_info = fetch_json(USER_INFO_URL.replace("USERNAME", username))
    if type(user_info) != int:
        userid = str(user_info["id"])
        folder = create_user_folder(userid)
        folderpath = folder[1]
        if folder[0] == 0:
            print(f"Local user data found at {folderpath}")
            if "user_info.json" in os.listdir(folderpath):
                if "multiplayer_rating.json" in os.listdir(folderpath):
                    with open(folderpath.joinpath("multiplayer_rating.json"), "r") as f:
                        multiplayer_rating_local = json.load(f)
                    multiplayer_rating = fetch_json(MP_RATING_URL.replace("USERID", userid))
                    if multiplayer_rating == multiplayer_rating_local:

                        pagenum = math.ceil(multiplayer_rating["RacesCompleted"]/100)
                        print(f"Pagenum: {pagenum}")
                        racescompleted = multiplayer_rating["RacesCompleted"]
                        print(f"RacesCompleted: {racescompleted}")

                        #TODO: go on with testing CareerPages.
                        for page in range(1, pagenum + 1):
                            entriesthispage_local = []
                            entriesthispage = []
                            print(f"Testing Page #{page}")
                            currentpage_local = folderpath.joinpath("CareerPages").joinpath(f"Page_{page}.json")
                            with open(currentpage_local, "r") as f:
                                currentpage_local_raw = json.load(f)
                            for c in currentpage_local_raw["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["Entries"]:
                                entriesthispage_local.append(c["RaceHash"])

                            currentpage = fetch_json(CAREER_PAGE_URL.replace("USERNAME", username).replace("PAGE", str(page)))
                            if type(currentpage) != int:
                                for c in currentpage["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["Entries"]:
                                    entriesthispage.append(c["RaceHash"])

                            print(f"Local racehashes:{len(entriesthispage_local)}\n{entriesthispage_local}")
                            print(f"Live racehashes:{len(entriesthispage)}\n{entriesthispage}")

                            if entriesthispage_local != entriesthispage:
                                save_json(folderpath.joinpath("CareerPages").joinpath(f"Page_{page}.json"), currentpage)
                                print(f"Page #{page} have been updated.")
                            else:
                                print(f"Page #{page} is up to date.")

                        print("local mp rating is up to date")
                        return
                    else:
                        print("Local mp-rating needs to be updated.")
                        with open(folderpath.joinpath("multiplayer_rating.json"), "w") as f:
                            json.dump(multiplayer_rating, f, indent=4)
                            print("Local mp-rating updated")
                else:
                    exit()
            else:
                exit()
        else:
            print(f"Setting up user data at {folder[1]}...Please wait.")
            multiplayer_rating = fetch_json(MP_RATING_URL.replace("USERID", userid))
            if type(multiplayer_rating) != int:
                save_json(folderpath.joinpath("user_info.json"), user_info)
                print("Saved user_info.json")
                save_json(folderpath.joinpath("multiplayer_rating.json"), multiplayer_rating)
                print("Saved multiplayer_rating.json")

                pagenum = math.ceil(multiplayer_rating["RacesCompleted"]/100)

                os.mkdir(folderpath.joinpath("CareerPages"))
                print("Created CareerPages folder.")
                for page in range(1, pagenum + 1):
                    page_n = fetch_json(CAREER_PAGE_URL.replace("USERNAME", username).replace("PAGE", str(page)))
                    save_json(folderpath.joinpath("CareerPages").joinpath(f"Page_{page}.json"), page_n)
                    print(f"Saved Page_{page}.json")

    else:
        return f"Error: Server is down or there is no such user as {username}"

#print("Test for Orban_k")
#start_download_pipeline("Orban_k")
print("\n")

print("Test for Bab_0")
start_download_pipeline("Bab_0")
print("\n")

#print("Test for Stoffie87")
#start_download_pipeline("Stoffie87")
print("\n")