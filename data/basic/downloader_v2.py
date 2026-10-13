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
  """Ezt a függvényt hívom be ha a felhasználó beír egy játékosnevet és a keresésre kattint az oldalon. Még nincs kész, nem tudom mit ad vissza."""
  # TODO: helyi mappák/fileok ellenőrzése.
  #  Ha van mappája, akkor valszeg már csak frissíteni kell a letöltött adatait.
  #  Megkell nézni, hogy a helyi user-info tartalma megegyezik-e az éppen file-al.
  #  Ezt a későbbiekben a többi file-al is elvégezni (mp rating, carr. page, stb).

  user_info = get_user_info(username)

  if user_info != 0:

    userid = user_info["id"]
    print(f"User found, ID: {userid}")
    multiplayer_rating = get_multiplayer_rating(userid)

    if type(multiplayer_rating) is not int:

      folder_user = folder_users.joinpath(str(userid))
      RacesCompleted = multiplayer_rating["RacesCompleted"]
      PageNum = [i for i in range(1,math.ceil(RacesCompleted/100)+1)]

      if not os.path.exists(folder_user):

        print(f"Creating user folder at {folder_user}")
        #os.mkdir(folder_user)
        #os.mkdir(folder_user.joinpath("CareerPages"))

        #with open(folder_user.joinpath("user_info.json"), "w", encoding="utf-8") as f:
          #json.dump(user_info, f, indent=4, ensure_ascii=False)
          #print(f"user_info.json saved at {folder_user}")

        #with open(folder_user.joinpath("multiplayer_rating.json"), "w", encoding="utf-8") as f:
          #json.dump(multiplayer_rating, f, indent=4, ensure_ascii=False)
          #print(f"multiplayer_rating.json saved at {folder_user}")
        print("Cancelling folder creation due to STOP (Standard Testing Operational Procedure).")



        print(f"User has {RacesCompleted} races, fetching {len(PageNum)} page(s) from;\n")

        #TODO: PAGE-EK LETÖLTÉSE

        page_urls = [f"https://game.raceroom.com/users/{username}/career?CurrentPage=-{n}&PageSize=100&json" for n in PageNum]
        pages = asyncio.run(main(page_urls, "page"))
        print(f"{len(pages)} page(s) are in memory atm.")
        racehashes = []

        for page in pages:
          print(f"Currently checking page {page["context"]["c"]["get"]["CurrentPage"]}")
          for line in page["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["Entries"]:
            if line["RaceHash"] not in racehashes:
              racehashes.append(line["RaceHash"])
          print(f"Racehashes found so far: {len(racehashes)}")
          print(f"Found {len(racehashes)} individual racehashes:")
          print(racehashes)

      #TODO: MÁR VAN HELYI FILEJA ÁG
      else:

        print("User folder found.")
        return
        #TODO: file-ok ellenőrzése, ha szükséges akkor a helyi file-ok frissítése, hiányzó fileok begyűjtése és letöltése.

    #TODO: NINCS MP RATING ÁG
    else:

      print(f"Error: User has no mp data or servers are down.")
      return multiplayer_rating

  #TODO: NEM LÉTEZŐ USER ÁG
  else:

    print("User not found")

async def fetch(s, url, request_type, retries, sleep_time):
    print(f"FETCHING: {url}")
    async with s.get(url) as r:
      raw_data = await r.json()
      time.sleep(sleep_time)
      if retries > 0:
        if request_type == "page" and r.status == 200:
          totalentries = raw_data["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["TotalEntries"]
          if totalentries > 0:
            print("Page loaded.")
            return raw_data
        else:
            print("Error fetching page.")
            return raw_data
      else:
        print("Error fetching page, out of retries.")
        return raw_data

async  def fetch_all(s, urls, request_type):
  tasks = []
  for url in urls:
    print(f"ON QUE: {url}")
    task = asyncio.create_task(fetch(s, url, request_type, 3, 0))
    tasks.append(task)
  print(f"FETCHING. PLEASE WAIT...")
  res = await asyncio.gather(*tasks)
  return res

async def main(urls, request_type):
  async with aiohttp.ClientSession() as session:
    start_time = time.time()
    jsons = await fetch_all(session, urls, request_type)
    end_time = time.time()
    print(f"Elapsed Time: {end_time - start_time}")
    return jsons

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