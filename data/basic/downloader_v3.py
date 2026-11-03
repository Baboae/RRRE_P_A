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

#region directories
dir_current = Path(os.getcwd())
dir_webapp = dir_current.parent.joinpath("webapp")
dir_static = dir_webapp.joinpath("static")
dir_users = dir_static.joinpath("users")
#endregion

async def fetch_url(url):
    response = await asyncio(requests.get(url))
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_static(username):
    local_users = os.listdir(dir_users)
    if username in local_users:
        print(os.listdir(f"{dir_users}/{username}"))

def download_pipeline(username):
    #region user-info, mp rating, avatar.webp asy
    check_static(username)




manual_testing = True
if manual_testing:
    dynamic = False
    if dynamic:
        username = input("Enter Username for testing: ")
    else:
        username = "Bab_0"
        print(f"Subject: {username}")
        download_pipeline(username)