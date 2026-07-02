#region Import
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List
#endregion

#region Player
@dataclass
class Player:
    user_id: str
    username: str
    full_name: str
    team: str
    country: str
    rat: float
    rep: float
    race_count: int
    global_position: int