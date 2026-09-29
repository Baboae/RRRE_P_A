#region imports
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import math
from pathlib import Path
#endregion
#region VERSION V1, WORKING, BUT SLOW.

BASE_DIR = Path(__file__).resolve().parent.parent.parent

session = requests.Session()

def fetch_json(data_url, t_out=10):
  attempts = 0
  max_retries = 10
  while attempts < max_retries:
    try:
      response = session.get(data_url, timeout=t_out)
      response.raise_for_status()

      if not response.text.strip():
        print("No data returned from the server.")
        return None
      try:
        data = response.json()
      except json.JSONDecodeError:
        print("Invalid JSON received")
        return None
      return data
    #region EXCEPTIONS
    except requests.exceptions.Timeout:
      attempts+=1
      time.sleep(1)
      print(f"Request timed out. \n Retrying. \n Attempt {attempts} out of {max_retries}.")

    except requests.exceptions.ConnectionError:
      print("Network error")
    except requests.exceptions.HTTPError as e:
      print(f"HTTP Error: {e}")
    except Exception as e:
      print(f"!!! UNEXPECTED ERROR, READ MORE !!!\n->\n{e}")
    #endregion

def save_json(data, filename, foldername):
  folder_path = os.path.join('/content', foldername)
  os.makedirs(folder_path, exist_ok=True)
  file_path = os.path.join(folder_path, filename)
  with open(file_path, 'w') as f:
    json.dump(data, f, indent=4)

def download_and_save_json(json_url, filename, foldername, t_out = 10):
  data = fetch_json(json_url, t_out)
  if data:
      save_json(data, filename, foldername)
      return f"OK: {filename}"
  return f"FAILED: {filename}"

def download_career_pages(username):
  user_info_url = f"https://game.raceroom.com/utils/user-info/{username}"
  user_info = fetch_json(user_info_url, t_out=5)

  if "error" in user_info:
    return [0, "No user found under this alias."]
  else:
    print("User found. Setting up folders and downloading data. Please wait.")
    userid = user_info["id"]
    user_folder = BASE_DIR / f"users/{username}_{userid}"
    save_json(user_info, "user_info.json", user_folder)

    try:
      user_mp_info = fetch_json(f"https://game.raceroom.com/multiplayer-rating/user/{userid}.json")
      if user_mp_info is None:
        return [0, "No ranked data found under this alias."]
      else:
        save_json(user_mp_info, "user_mp_info.json", user_folder)
        RacesCompleted = user_mp_info["RacesCompleted"]
        NumberOfPages = math.ceil(RacesCompleted / 100)
        start = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
          futures = {executor.submit(download_and_save_json,
                                     f"https://game.raceroom.com/users/{username}/career?CurrentPage=-{i}&PageSize=100&json",
                                     f"Page_{i}.json", user_folder / "CareerPages", t_out=10): i for i in
                     range(1, NumberOfPages + 1)}
          for future in as_completed(futures):
            print(future.result())
        print(f"Downloading: {time.time() - start:.2f}s")

        career_pages_folder = user_folder / "CareerPages"
        career_pages_filenames = [f for f in os.listdir(career_pages_folder) if f.endswith(".json")]

        RaceHashes = []
        for filename in career_pages_filenames:
          with open(os.path.join(career_pages_folder, filename), "r") as f:
            data = json.load(f)
            races = data["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["Entries"]
            for race in races:
              if race["RaceHash"] not in RaceHashes:
                RaceHashes.append(race["RaceHash"])
        return [1, user_folder]
    except Exception as e:
      return [0, "Error. Something went wrong."]
#endregion