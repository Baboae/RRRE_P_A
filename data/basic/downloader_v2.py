#region IMPORTOK
import os
import math
import time
import json
import asyncio
from pathlib import Path

import aiohttp
import requests
#endregion

#region konfig, mappa elérések
MAX_CONCURRENT = 10      # egyszerre max ennyi kérés (ha még mindig timeout van, vedd lejjebb: 5)
RETRIES = 3
TIMEOUT = aiohttp.ClientTimeout(total=60, connect=20)

curdir = Path(os.getcwd())
print(curdir)

# pycharm
folder_users = curdir.parent.joinpath("webapp", "static", "users")
# colab
# folder_users = curdir.joinpath("webapp", "static", "users")
save_racelogs_at = curdir.parent.joinpath("webapp", "static", "racelogs")

folder_users.mkdir(parents=True, exist_ok=True)
save_racelogs_at.mkdir(parents=True, exist_ok=True)
local_users = os.listdir(folder_users)

print(save_racelogs_at)
#endregion

#region fgv-ek és download pipeline
def get_user_info(username):
  """Visszaadja a user-info json-t, vagy 0-t ha nincs kapcsolat / nincs ilyen user."""
  response = requests.get(f"https://game.raceroom.com/utils/user-info/{username}", timeout=20)
  if response.status_code != 200:
    return 0
  data = response.json()
  if "error" in data:
    return 0
  return data

def get_multiplayer_rating(userid):
  """Visszaadja az mp rating json-t, vagy a státuszkódot (int) ha nem sikerült."""
  response = requests.get(f"https://game.raceroom.com/multiplayer-rating/user/{userid}.json", timeout=20)
  if response.status_code != 200:
    return response.status_code
  return response.json()

def download_pipeline(username):
  """Akkor hívom, ha a felhasználó beír egy játékosnevet és keres. Még nincs kész, nem tudom mit ad vissza."""
  # TODO: helyi mappák/fileok ellenőrzése, frissítés a többi fájlra is (carr. page, stb).

  user_info = get_user_info(username)
  if user_info == 0:
    print("User not found")
    return

  username = user_info["username"]  # az eredeti írásmódra frissítés
  userid = user_info["id"]
  print(f"User found, ID: {userid}")

  live_multiplayer_rating = get_multiplayer_rating(userid)
  if type(live_multiplayer_rating) is int:
    print("Error: User has no mp data or servers are down.")
    return live_multiplayer_rating

  folder_user = folder_users.joinpath(username)  # vagy -> str(userid) ?
  races_completed = live_multiplayer_rating["RacesCompleted"]
  page_nums = list(range(1, math.ceil(races_completed / 100) + 1))

  if not folder_user.exists():
    print(f"Creating user folder at {folder_user}")
    folder_user.mkdir()
    save_pages_at = folder_user.joinpath("CareerPages")
    save_pages_at.mkdir()

    with open(folder_user.joinpath("user_info.json"), "w", encoding="utf-8") as f:
      json.dump(user_info, f, indent=4, ensure_ascii=False)
      print(f"user_info.json saved at {folder_user}")

    avatar = requests.get(user_info["avatar"], timeout=20).content
    with open(folder_user.joinpath("avatar.webp"), "wb") as f:
      f.write(avatar)
      print(f"avatar.webp saved at {folder_user}")

    with open(folder_user.joinpath("multiplayer_rating.json"), "w", encoding="utf-8") as f:
      json.dump(live_multiplayer_rating, f, indent=4, ensure_ascii=False)
      print(f"multiplayer_rating.json saved at {folder_user}")

    pages = asyncio.run(download_pages(page_nums, username, save_pages_at))
    pages = [p for p in pages if p is not None]  # a sikertelen oldalak None-ok

    users_racehashes = []
    seen = set()
    for page in pages:
      for line in page["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["Entries"]:
        racehash = line["RaceHash"]
        if racehash not in seen:
          seen.add(racehash)
          users_racehashes.append(racehash)
    print(f"User has {len(users_racehashes)} races.")

    downloaded_racehashes = {Path(f).stem for f in os.listdir(save_racelogs_at)}
    print(f"Downloaded races: {len(downloaded_racehashes)}")
    racehashes_to_download = [h for h in users_racehashes if h not in downloaded_racehashes]
    print(f"Racehashes to download: {len(racehashes_to_download)}")

    racelogs = asyncio.run(download_racelogs(racehashes_to_download, save_racelogs_at))
    failed = sum(1 for r in racelogs if r is None)
    print(f"Download finished! Local Racelogs: {len(os.listdir(save_racelogs_at))} (failed: {failed})")
  else:
    print("User folder already exists.")
    with open(folder_user.joinpath("multiplayer_rating.json"), "r", encoding="utf-8") as f:
      local_multiplayer_rating = json.load(f)

    print("Validating multiplayer_rating.json")
    mpr_needs_update = False
    if live_multiplayer_rating.keys() != local_multiplayer_rating.keys():
      print("Missing keys in multiplayer_rating.json")
      mpr_needs_update = True
    else:
      for key in live_multiplayer_rating.keys():
        if live_multiplayer_rating[key] != local_multiplayer_rating[key]:
          print(f"Updating {key}")
          mpr_needs_update = True
    if mpr_needs_update:
      with open(folder_user.joinpath("multiplayer_rating.json"), "w", encoding="utf-8") as f:
        json.dump(live_multiplayer_rating, f, indent=4, ensure_ascii=False)
        print("MPR updated.")
#endregion

#region async letöltő fgv-ek
async def get_json(s, sem, url, retries=RETRIES):
  """Közös letöltő: szemafor + újrapróbálkozás exponenciális várakozással. Siker esetén json, különben None."""
  for attempt in range(retries):
    try:
      async with sem:
        async with s.get(url) as r:
          if r.status == 200:
            return await r.json(content_type=None)
          print(f"{url} -> STATUS {r.status} ({attempt + 1}/{retries})")
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
      print(f"{url} -> {type(e).__name__} ({attempt + 1}/{retries})")
    await asyncio.sleep(2 ** attempt)
  print(f"{url} -> feladva")
  return None

#region racelog letöltések
async def fetch_racelog(s, sem, racehash, save_at):
  raw_data = await get_json(s, sem, f"https://game.raceroom.com/multiplayer/results/{racehash}")
  if raw_data is None:
    return None
  with open(save_at.joinpath(f"{racehash}.json"), "w", encoding="utf-8") as f:
    json.dump(raw_data, f, indent=4, ensure_ascii=False)
  return raw_data
async def download_racelogs(racehashes, save_at):
  sem = asyncio.Semaphore(MAX_CONCURRENT)
  connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT)
  async with aiohttp.ClientSession(timeout=TIMEOUT, connector=connector) as session:
    start_time = time.time()
    tasks = [fetch_racelog(session, sem, h, save_at) for h in racehashes]
    allracelogs = await asyncio.gather(*tasks)
    print(f"\nELAPSED TIME: {time.time() - start_time}\n")
    return allracelogs
#endregion
#region page letöltések
async def fetch_page(s, sem, page, username, save_at):
  url = f"https://game.raceroom.com/users/{username}/career?CurrentPage=-{page}&PageSize=100&json"
  raw_data = await get_json(s, sem, url)
  if raw_data is None:
    return None
  totalentries = raw_data["context"]["c"]["raceList"]["GetUserMpRatingProgressResult"]["TotalEntries"]
  if totalentries <= 0:
    print(f"Page #{page} -> BAD (üres)")
    return None
  with open(save_at.joinpath(f"page_{page}.json"), "w", encoding="utf-8") as f:
    json.dump(raw_data, f, indent=4, ensure_ascii=False)
  print(f"Page #{page} -> OK, saved")
  return raw_data
async def download_pages(pages, username, save_at):
  sem = asyncio.Semaphore(MAX_CONCURRENT)
  connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT)
  async with aiohttp.ClientSession(timeout=TIMEOUT, connector=connector) as session:
    start_time = time.time()
    tasks = [fetch_page(session, sem, p, username, save_at) for p in pages]
    allpages = await asyncio.gather(*tasks)
    print(f"\nELAPSED TIME: {time.time() - start_time}\n")
    return allpages
#endregion
#endregion

dynamictest = True

if dynamictest:
  #region Dinamikus teszt:
  username = input("Enter username:")
  start_time = time.time()
  print("\n")
  download_pipeline(username)
  print(f"TOTAL ELAPSED TIME: {time.time() - start_time}\n")
  #endregion
else:
  #region statikus teszt fix user-ekkel:
  start_time = time.time()
  usernames = ["Bab_0", "Enzo_Philippau", "ooxx", "orban_k"]  # seuser, manolensen - bugos ?
  for user in usernames:
    download_pipeline(user)
  print(f"TOTAL ELAPSED TIME: {time.time() - start_time}\n")
  #endregion