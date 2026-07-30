import json
import os
import requests
from datetime import datetime

TOKEN = os.environ["BOT_TOKEN"]

# Read state
with open("state.json") as f:
    state = json.load(f)

last_update_id = state["last_update_id"]

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

response = requests.get(
    url,
    params={
        "offset": last_update_id + 1
    }
)

data = response.json()

print("Telegram response received")

if data["ok"]:
    updates = data["result"]

    print(f"New messages found: {len(updates)}")

    if updates:
        latest_update_id = updates[-1]["update_id"]

        # Save our new bookmark
        state["last_update_id"] = latest_update_id

        with open("state.json", "w") as f:
            json.dump(state, f, indent=2)

        # Load journal
        with open("journal.json") as f:
            journal = json.load(f)

        for update in updates:
            message = update.get("message", {})

            sender = message.get("from", {}).get("first_name", "Unknown")

            entry = {
                "date": datetime.fromtimestamp(message.get("date")).strftime("%Y-%m-%d"),
                "sender": sender,
                "question": state["last_question"],
            }

            if "text" in message:
                entry["type"] = "text"
                entry["response"] = message["text"]

            elif "video" in message:
                entry["type"] = "video"
                entry["response"] = message["video"]["file_id"]

            elif "voice" in message:
                entry["type"] = "voice"
                entry["response"] = message["voice"]["file_id"]

            elif "photo" in message:
                entry["type"] = "photo"
                entry["response"] = message["photo"][-1]["file_id"]

            else:
                entry["type"] = "other"
                entry["response"] = "Unsupported message type"

            journal.append(entry)

            print("Saved:", entry["type"], "from", sender)

        # Save journal
        with open("journal.json", "w") as f:
            json.dump(journal, f, indent=2)

else:
    print("Telegram returned an error:")
    print(data)
