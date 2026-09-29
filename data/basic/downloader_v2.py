#region TASK:
#TODO
#pass the input from the form (username)
#check if user is valid (basically if the site gives a resp. or not)
#download and save user-info and mp-rating (if they have mp-rating) JSON files under ...webapp/static/users/{username_userid}

#URL for the user-info: https://game.raceroom.com/utils/user-info/{username}
#URL for the mp-rating: https://game.raceroom.com/multiplayer-rating/user/{userid}.json

#once the 2 JSON files are downloaded, from the mp-rating file check how much race the user has

#with every 100 race, 1 page of RaceHashes (basically an id for every race) generates in a paged JSON file formula
#for example, 64 race means 1 page, 128 means 2 page and 1125 race is stored in 12 pages, starting from -1 to -n.

#based on the num of races the page num can be calculated w:
#-> NumOfPages=math.ceil(num of races / 100)

#download all pages

#URL for pages: https://game.raceroom.com/users/{username}/career?CurrentPage=-{NumOfPages}&PageSize=100&json
#save all page JSON files at ...webapp/static/users/{username_userid}/pages
#endregion

import os
import json
import math
from idlelib.debugobj_r import remote_object_tree_item
from pathlib import Path
from sys import excepthook

import requests
from conda.exports import root_dir

app_folder=Path(__file__).parent.parent.parent

USER_INFO_URL = "https://game.raceroom.com/utils/user-info/USERNAME"
MP_RATING_URL = "https://game.raceroom.com/multiplayer-rating/user/USERID.json"
CAREER_PAGE_URL = "https://game.raceroom.com/users/USERNAME/career""?CurrentPage=-NUMOFPAGES&PageSize=100&json"

def fetch_json(URL):
    response = requests.get(URL)
    if response.status_code == 200 and "error" not in response.json().keys():
        return response.json()
    else:
        return response.status_code
def create_user_folder(userid, username, racescompleted):
    userfolder = app_folder.joinpath("data").joinpath("webapp").joinpath("users").joinpath(f"{userid}_{username}_{racescompleted}")
    if not os.path.exists(userfolder):
        os.makedirs(userfolder)
    else:
        return 1
    return userfolder

def start_download_pipeline(username):
    errormsg = ""
    try:
        user_info=fetch_json(USER_INFO_URL.replace("USERNAME", username))
        if type(user_info) == int:
            errormsg = f"No user named {username}."
            raise Exception
        else:
            username = user_info["username"]
            print(f"Found: {username}")
            userid = user_info["id"]
            print("id: ", userid)
            mp_rating = fetch_json(MP_RATING_URL.replace("USERID", str(userid)))
            if type(mp_rating) == int:
                errormsg = f"No Mp-rating found for {username}."
                raise Exception
            else:
                print("MP ratings found.")
                racescompleted = mp_rating["RacesCompleted"]
                userfolder = create_user_folder(userid, username, racescompleted)
                if userfolder == 1:
                    print("User folder already exists.")
                else:
                    print(f"User folder created at {userfolder}")
    except Exception:
        return errormsg

username = input("Enter username for manual testing:")
print(start_download_pipeline(username))
#print(fetch_json(USER_INFO_URL.replace("USERNAME", username)))