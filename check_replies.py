import json
import os
import requests

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

        for update in updates:
            message = update.get("message", {})

            sender = message.get("from", {}).get("first_name", "Unknown")

            print("Sender:", sender)

            if "text" in message:
                print("Text:", message["text"])

            elif "video" in message:
                print("Received a video")

            elif "voice" in message:
                print("Received a voice message")

            elif "photo" in message:
                print("Received a photo")

            else:
                print("Received another type of message")

else:
    print("Telegram returned an error:")
    print(data)
