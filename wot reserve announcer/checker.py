import os
import json
import requests
from datetime import datetime, timezone

WG_APP_ID = os.environ["WG_APP_ID"]
WG_TOKEN = os.environ["WG_TOKEN"]
CLAN_ID = os.environ["CLAN_ID"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

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

    r = requests.post(
        DISCORD_WEBHOOK,
        json=payload
    )

    r.raise_for_status()


def format_time(timestamp):
    dt = datetime.fromtimestamp(
        timestamp,
        timezone.utc
    )

    return dt.strftime("%H:%M UTC")


def main():

    old_state = load_state()
    new_state = {}

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

                # New activation detected
                if old_state.get(reserve_id) != activation:

                    bonus_text = ""

                    for bonus in item.get("bonus_values", []):
                        bonus_text += (
                            f"• {bonus['battle_type']}: "
                            f"+{int(bonus['value']*100)}%\n"
                        )

                    message = (
                        "🚨 **CLAN RESERVE ACTIVE** 🚨\n\n"
                        f"💰 **{reserve['name']}**\n"
                        f"Level {item['level']}\n\n"
                        "**Bonus:**\n"
                        f"{bonus_text}\n"
                        f"⏳ Duration: "
                        f"{item['action_time']//3600} hours\n"
                        f"🕒 Ends: "
                        f"{format_time(item['active_till'])}\n\n"
                        "Happy farming, commanders! 🫡"
                    )

                    send_discord(message)

    save_state(new_state)


if __name__ == "__main__":
    main()