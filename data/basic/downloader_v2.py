import os
import math
import time
import json
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

def fetching(url):
  response = requests.get(url)
  if response.status_code != 200:
    return response.status_code
  else:
    return response.json()

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
def get_pages(page_urls):
  """Letölti a felhasználó "'career pages' json-jait.
    bemenetként megkapja listában az url-eket amiket le kell töltenie."""
  #TODO: valamilyen multiprocess/multithreading függvényt megírni,
  # amivel egyszerre több request-et leadva a raceroom szerverekre
  # egyszerre letöltjük az összes json-t.
  downloaded_pages = []
  if len(page_urls) <=9:
    mw = (math.ceil(len(page_urls)/4))
  else:
      mw = len(page_urls)
  with concurrent.futures.ThreadPoolExecutor(max_workers=mw) as executor:
    # Start the load operations and mark each future with its URL
    start_time = time.time()
    future_to_url = {executor.submit(fetching, url): url for url in page_urls}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
            if type(data) is int:
              raise Exception
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))
        else:
            print('%r page is %d bytes' % (url, len(data)))
            #print(data)
            downloaded_pages.append(data)
    end_time = time.time()
    print(f"Download done in {end_time - start_time}s")
    return downloaded_pages
def download_pipeline(username):
  """Ezt a függvényt hívom be ha a felhasználó beír egy játékosnevet és a keresésre kattint az oldalon. Még nincs kész, nem tudom mit ad vissza."""
  user_info = get_user_info(username)

  if user_info != 0:

    #TODO: helyi mappák/fileok ellenőrzése.
    # Ha van mappája, akkor valszeg már csak frissíteni kell a letöltött adatait.
    # Megkell nézni, hogy a helyi user-info tartalma megegyezik-e az éppen file-al.
    # Ezt a későbbiekben a többi file-al is elvégezni (mp rating, carr. page, stb).

    userid = user_info["id"]
    print(userid)
    multiplayer_rating = get_multiplayer_rating(userid)

    if type(multiplayer_rating) is not int:

      folder_user = folder_users.joinpath(str(userid))
      RacesCompleted = multiplayer_rating["RacesCompleted"]
      PageNum = [i for i in range(1,math.ceil(RacesCompleted/100)+1)]

      if not os.path.exists(folder_user):

        print(f"Created user folder at {folder_user}\n#kappa")

        os.mkdir(folder_user)
        os.mkdir(folder_user.joinpath("CareerPages"))

        print(f"{RacesCompleted} Races completed, Downloading {len(PageNum)} Page   from;")
        print(f"{get_pages(username, PageNum)}")

        with open(folder_user.joinpath("user_info.json"), "w", encoding="utf-8") as f:
          json.dump(user_info, f, indent=4, ensure_ascii=False)

        with open(folder_user.joinpath("multiplayer_rating.json"), "w", encoding="utf-8") as f:
          json.dump(multiplayer_rating, f, indent=4, ensure_ascii=False)
        #TODO: get_pages megírása, majd behívása


      else:

        print("User folder found.")
        return
        #TODO: file-ok ellenőrzése, ha szükséges akkor a helyi file-ok frissítése, hiányzó fileok begyűjtése és letöltése.

    else:

      print(f"Error: User has no mp data or servers are down.")
      return multiplayer_rating

  else:

    print("User not found")



async def fetch(s, url):
  async with s.get(url) as r:
    #print(f"fetching {url}")
    if r.status != 200:
      r.raise_for_status()
    return await r.json()

async  def fetch_all(s, urls):
  tasks = []
  for url in urls:
    task = asyncio.create_task(fetch(s, url))
    tasks.append(task)
  res = await asyncio.gather(*tasks)
  return res

async def main(urls):
  async with aiohttp.ClientSession() as session:
    htmls = await fetch_all(session, urls)
    racehashes = []
    for page in htmls:
      for line in page["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["Entries"]:
        if line["RaceHash"] not in racehashes:
          racehashes.append(line["RaceHash"])
    print(len(racehashes))
    print(racehashes)

if __name__ == "__main__":
  start = perf_counter()
  username = "Stoffie87"
  urls = [f"https://game.raceroom.com/users/{username}/career?CurrentPage=-{i}&PageSize=100&json" for i in range(1,28)]

  asyncio.run(main(urls))


  stop = perf_counter()
  print(f"Time taken: {stop - start}")
#region statikus teszt:
#username = "manolensen"
#pagenums = [i for i i0n range(1,41)]
#endregion

#region Dinamikus teszt:
#username = input("Enter username:")
#download_pipeline(username)
#endregion