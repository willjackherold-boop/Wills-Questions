import json
import os
import requests
import gspread
from datetime import datetime
from pathlib import Path
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PARTNER_CHAT_ID = 8698319651

TOKEN = os.environ["BOT_TOKEN"]

ROOT_FOLDER_ID = "1tI4epNzaneuAdRjlPr7gsBKIoYvn4rwm"
VIDEO_FOLDER_ID = "1cY6XJU-zO_7zTaBD542NY1MBJOv1nd18"
VOICE_FOLDER_ID = "1m3nszPEfumv4grZWJJ0G8t3HLoQNs-FG"

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

DRIVE_TOKEN = json.loads(os.environ["GOOGLE_DRIVE_TOKEN"])

drive_credentials = UserCredentials.from_authorized_user_info(
    DRIVE_TOKEN,
    ["https://www.googleapis.com/auth/drive"]
)

drive_service = build(
    "drive",
    "v3",
    credentials=drive_credentials
)

SPREADSHEET_ID = "1i4nj_eFeuhzbfI7FAwjz-1hsK4STxhbA1T0xNDFgL-I"

sheet = client.open_by_key(SPREADSHEET_ID).sheet1

def download_telegram_file(file_id, filename):
    file_info_url = f"https://api.telegram.org/bot{TOKEN}/getFile"

    response = requests.get(
        file_info_url,
        params={"file_id": file_id}
    )

    response.raise_for_status()

    file_path = response.json()["result"]["file_path"]

    download_url = (
        f"https://api.telegram.org/file/"
        f"bot{TOKEN}/{file_path}"
    )

    file_response = requests.get(download_url)
    file_response.raise_for_status()

    file_data = file_response.content

    with open(filename, "wb") as f:
        f.write(file_data)

    return filename

def upload_to_drive(filename, folder_id):

    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    media = MediaFileUpload(
        filename,
        resumable=True
    )

    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = uploaded.get("id")

    # Make file viewable by link
    drive_service.permissions().create(
        fileId=file_id,
        body={
            "type": "anyone",
            "role": "reader"
        }
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    
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

                file_id = message["video"]["file_id"]

                filename = f"video_{message['date']}.mp4"

                local_file = download_telegram_file(
                    file_id,
                    filename
                )

                entry["response"] = upload_to_drive(
                    local_file,
                    VIDEO_FOLDER_ID
                )

                os.remove(local_file)

            elif "video_note" in message:
                entry["type"] = "video_note"

                file_id = message["video_note"]["file_id"]

                filename = f"video_note_{message['date']}.mp4"

                local_file = download_telegram_file(
                    file_id,
                    filename
                )
            
                entry["response"] = upload_to_drive(
                    local_file,
                    VIDEO_FOLDER_ID
                )

                os.remove(local_file)

            elif "voice" in message:
                entry["type"] = "voice"
            
                file_id = message["voice"]["file_id"]
            
                filename = f"voice_{message['date']}.ogg"
            
                local_file = download_telegram_file(
                    file_id,
                    filename
                )
            
                entry["response"] = upload_to_drive(
                    local_file,
                    VOICE_FOLDER_ID
                )

                os.remove(local_file)

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
