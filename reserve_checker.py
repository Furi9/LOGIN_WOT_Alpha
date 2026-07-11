import os
import json
import requests
import pytz
from datetime import datetime, timezone


def allowed_time():
    timezone = pytz.timezone("Europe/Prague")
    now = datetime.now(timezone)

    return 12 <= now.hour < 24


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
        "en": {
            "active": "🚨 **CLAN RESERVE ACTIVE** 🚨",
            "level": "Level",
            "bonus": "**Bonus:**",
            "duration": "⏳ Duration:",
            "ends": "🕒 Ends:",
            "footer": "Happy farming, commanders! 🫡"
        },

        "cs": {
            "active": "🚨 **Zálohy běží!** 🚨",
            "level": "Úroveň",
            "bonus": "**Bonus:**",
            "duration": "⏳ Doba trvání:",
            "ends": "🕒 Končí:",
            "footer": ""
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

    r = requests.post(
        DISCORD_WEBHOOK,
        json=payload
    )

    r.raise_for_status()


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

    messages = []
        if not allowed_time():
            print("Outside Czech reserve hours. Exiting.")
            return

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
                    #if old_state.get(reserve_id) != activation:
                    if True:

                        msg = MESSAGES[LANGUAGE]

                        message = (
                            f"{reserve_icon(reserve['name'])} **{RESERVE_TRANSLATIONS.get(reserve['name'], reserve['name'])}**\n"
                            f"🕒 Končí: {format_time(item['active_till'])}"
                        )

                        messages.append(message)
    if messages:
        send_discord(
            f"{msg['active']}\n\n" +
            "\n\n".join(messages)
        )

    save_state(new_state)


if __name__ == "__main__":
    main()