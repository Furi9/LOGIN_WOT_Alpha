import os
import json
import requests
import pytz
from datetime import datetime, timezone


def allowed_time():
    tz = pytz.timezone("Europe/Prague")
    now = datetime.now(tz)

    return 15 <= now.hour <= 23


WG_APP_ID = os.environ["WG_APP_ID"]
WG_TOKEN = os.environ["WG_TOKEN"]
CLAN_ID = os.environ["CLAN_ID"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]


RESERVE_TRANSLATIONS = {
    "Battle Payments": "Kredity",
    "Additional Briefing": "Zkušenosti posádky",
    "Tactical Training": "Bojové zkušenosti",
    "Military Maneuvers": "Volné zkušenosti",
}


BATTLE_TRANSLATIONS = {
    "All Battles": "Všechny bitvy",
    "Random Battles": "Náhodné bitvy",
    "Clan Battles and Tournaments": "Klanové bitvy a turnaje",
    "Skirmishes and Battles for Stronghold": "Střety a bitvy o pevnost"
}


LANGUAGE = "cs"


MESSAGES = {
    "cs": {
        "active": "🚨 **Zálohy běží!** 🚨",
        "ends": "🕒 Končí:"
    },

    "en": {
        "active": "🚨 **CLAN RESERVE ACTIVE** 🚨",
        "ends": "🕒 Ends:"
    }
}


STATE_FILE = "reserve_state.json"

API_URL = "https://api.worldoftanks.eu/wot/stronghold/clanreserves/"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_reserves():

    params = {
        "application_id": WG_APP_ID,
        "access_token": WG_TOKEN,
        "clan_id": CLAN_ID
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise Exception(data)

    return data["data"]


def send_discord(message):

    payload = {
        "content": message
    }

    response = requests.post(
        DISCORD_WEBHOOK,
        json=payload
    )

    response.raise_for_status()


def reserve_icon(name):

    if "Battle Payments" in name:
        return "💰"

    if "Briefing" in name:
        return "👨‍✈️"

    if "Training" in name:
        return "⭐"

    if "Maneuvers" in name:
        return "📚"

    return "🎁"


def format_time(timestamp):

    tz = pytz.timezone("Europe/Prague")

    dt = datetime.fromtimestamp(
        timestamp,
        timezone.utc
    ).astimezone(tz)

    return dt.strftime("%H:%M %Z")
def main():

    if not allowed_time():
        print("Outside Czech reserve hours. Exiting.")
        return

    old_state = load_state()
    new_state = {}
    messages = []

    reserves = get_reserves()

    for reserve in reserves:

        for item in reserve.get("in_stock", []):

            if item.get("status") == "active":

                reserve_id = (
                    reserve["type"]
                    + "_"
                    + str(item["level"])
                )

                activation = item.get("activated_at")
                new_state[reserve_id] = activation

                if old_state.get(reserve_id) != activation:

                    message = (
                        f"{reserve_icon(reserve['name'])} "
                        f"**{RESERVE_TRANSLATIONS.get(reserve['name'], reserve['name'])}**\n"
                        f"{MESSAGES[LANGUAGE]['ends']} "
                        f"{format_time(item['active_till'])}"
                    )

                    messages.append(message)


save_state(new_state)

if messages:
    final_message = (
        f"{MESSAGES[LANGUAGE]['active']}\n\n"
        + "\n\n".join(messages)
    )

    send_discord(final_message)

import time

if __name__ == "__main__":
    print("WoT Reserve Checker started")

    while True:
        try:
            main()
        except Exception as e:
            print("Error:", e)

        time.sleep(300)