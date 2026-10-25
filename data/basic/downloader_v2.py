import os
import math
import random
import time
import json
from multiprocessing import resource_tracker
from time import perf_counter

import aiohttp
import requests
import asyncio
import concurrent.futures
from pathlib import Path


curdir = Path(os.getcwd())
folder_users = curdir.parent.joinpath("webapp").joinpath("static").joinpath("users")
local_users = [user for user in os.listdir(folder_users)]

#print(local_users)

def get_user_info(username):
  """A kapott felhasználónevet beilleszti a linkbe. Ha van kapcsolat és nincs 'error' kulcs az json-ban, akkor visszaadja a nyers json-t, egyébként nullát dob. """

  response = requests.get(f"https://game.raceroom.com/utils/user-info/{username}")
  if response.status_code != 200 or "error" in response.json().keys():
    return 0
  else:
    return response.json()
def get_multiplayer_rating(userid):
  """Kap egy userid-t, linkbe pattintja, ha az ad választ akkor visszaadja a nyers json-t, amúgy a státuszkódot.  """

  response = requests.get(f"https://game.raceroom.com/multiplayer-rating/user/{str(userid)}.json")
  if response.status_code != 200:
    return response.status_code
  else:
    return response.json()

def download_pipeline(username):
  #region docstring + kind reminder
  """Ezt a függvényt hívom be ha a felhasználó beír egy játékosnevet és a keresésre kattint az oldalon. Még nincs kész, nem tudom mit ad vissza."""
  # TODO: helyi mappák/fileok ellenőrzése:
  #  Ha van mappája, akkor valszeg már csak frissíteni kell a letöltött adatait.
  #  Megkell nézni, hogy a helyi user-info tartalma megegyezik-e az éppen file-al.
  #  Ezt a későbbiekben a többi file-al is elvégezni (mp rating, carr. page, stb).
  #endregion

  user_info = get_user_info(username)
  if user_info != 0:

    userid = user_info["id"]
    print(f"User found, ID: {userid}")
    multiplayer_rating = get_multiplayer_rating(userid)

    if type(multiplayer_rating) is not int:

      folder_user = folder_users.joinpath(username) #ha az userid lenne a mappanév: str(userid)
      races_completed = multiplayer_rating["RacesCompleted"]
      print(f"Races Completed(live): {races_completed}")
      page_nums = [i for i in range(1,math.ceil(races_completed/100)+1)]

      #MAPPA LÉTREHOZÁS, be és letöltés.
      if not os.path.exists(folder_user):
        #region mappalétrehozás, user, mp inf. letöltés
        print(f"Creating user folder at {folder_user}")
        os.mkdir(folder_user)
        save_pages_at = folder_user.joinpath("CareerPages")
        os.mkdir(save_pages_at)
        with open(folder_user.joinpath("user_info.json"), "w", encoding="utf-8") as f:
          json.dump(user_info, f, indent=4, ensure_ascii=False)
          print(f"user_info.json saved at {folder_user}")

        with open(folder_user.joinpath("multiplayer_rating.json"), "w", encoding="utf-8") as f:
          json.dump(multiplayer_rating, f, indent=4, ensure_ascii=False)
          print(f"multiplayer_rating.json saved at {folder_user}")
        #endregion
        #region page-ek, racelogok letöltése, mentése
        asyncio.run(download_pages(page_nums, username, save_pages_at))
        #endregion
      else:
        # TODO: MÁR VAN HELYI FILEJA ÁG
        print("User folder found.")
        with open(folder_user.joinpath("multiplayer_rating.json"), "r", encoding="utf-8") as f:
          local_mp_r = json.load(f)
          print(f"Races Completed(local): {local_mp_r["RacesCompleted"]}")
          if local_mp_r != multiplayer_rating:
            print(f"Local mp-rating is outdated, update required.\nLOCAL:\n{local_mp_r}\nLIVE:\n{multiplayer_rating}")
            if local_mp_r["RacesCompleted"] != multiplayer_rating["RacesCompleted"]: #vagy: rating, rep
              print("Races completed do not match, updating...")
            else:
              print("General mp rating data out of data, refreshing the local mp-rating file...")
              with open(folder_user.joinpath("multiplayer_rating.json"), "w", encoding="utf-8") as wf:
                wf.write(json.dumps(multiplayer_rating, indent=4, ensure_ascii=False))
    else:
      # TODO: NINCS MP RATING ÁG
      print(f"Error: User has no mp data or servers are down.")
      return multiplayer_rating
  else:
    # TODO: NEM LÉTEZŐ USER ÁG
    print("User not found")

async def fetch_page(s, page, username, save_at, sleep_time=0, retries = 3):
  url = f"https://game.raceroom.com/users/{username}/career?CurrentPage=-{page}&PageSize=100&json"
  async with s.get(url) as r:
    body = await r.read()
    raw_data = await r.json()
    await asyncio.sleep(sleep_time)

    if retries > 0:
      if r.status == 200:
        totalentries = raw_data["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["TotalEntries"]
        size = round(len(body) * (10 ** -6), 3)
        if totalentries > 0:
          print(f"\nPage #{page} -> OK\nSIZE: {size}")
          with open(save_at.joinpath(f"page_{page}.json"), "w", encoding="utf-8") as f:
            json.dump(raw_data, f, indent=4, ensure_ascii=False)
          # nyers adat kimentése + vmit visszaadni (?)
          return raw_data
        else:
          # valamilyen errorhandling+rekurziós újrapróbálkozás (?) lol
          print(f"\nPage #{page} -> BAD")
      else:
        print(f"\nError connecting to Page #{page}")
        await fetch_page(s, page, username, sleep_time + 1, retries - 1)
    else:
      print(f"Error connecting to Page #{page}, out of retries.")

async def fetch_pages(s, pages, username, save_at):
  tasks = []
  for page in pages:
    task = asyncio.create_task(fetch_page(s, page, username, save_at))
    tasks.append(task)
  res = await asyncio.gather(*tasks)
  return res

async def download_pages(pages, username, save_at):
  async with aiohttp.ClientSession() as session:
    start_time = time.time()
    allpages = await fetch_pages(session, pages, username, save_at)
    end_time = time.time()
    print(f"\nELAPSED TIME:{end_time - start_time}\n")
    return allpages

if __name__ == "__main__":
  #start = perf_counter()
  #urls = []
  #asyncio.run(main(urls))
  #stop = perf_counter()
  #print(f"Time taken: {stop - start}")
  pass

#region Dinamikus teszt:
username = input("Enter username:")
print("\n")
download_pipeline(username)
#endregion