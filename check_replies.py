import json
import os
import requests
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

PARTNER_CHAT_ID = 7915079835

TOKEN = os.environ["BOT_TOKEN"]

GOOGLE_CREDENTIALS = json.loads(os.environ["GOOGLE_CREDENTIALS"])

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(
    GOOGLE_CREDENTIALS,
    scopes=SCOPES
)

client = gspread.authorize(credentials)

SPREADSHEET_ID = "1i4nj_eFeuhzbfI7FAwjz-1hsK4STxhbA1T0xNDFgL-I"

sheet = client.open_by_key(SPREADSHEET_ID).sheet1

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

            if message.get("chat", {}).get("id") != PARTNER_CHAT_ID:
                print("Ignoring message from another user")
                continue

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

            elif "video_note" in message:
                entry["type"] = "video_note"
                entry["response"] = message["video_note"]["file_id"]

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

sheet.append_row([
    entry["date"],
    entry["sender"],
    entry["question"],
    entry["type"],
    entry["response"]
])

print("Saved:", entry["type"], "from", sender)

# Save journal
with open("journal.json", "w") as f:
    json.dump(journal, f, indent=2)
    
else:
    print("Telegram returned an error:")
    print(data)
