import csv
import json
import os
import requests
from datetime import datetime, timezone

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Read questions
with open("questions.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    questions = [row[list(row.keys())[0]] for row in reader]

# Read state
with open("state.json") as f:
    state = json.load(f)

index = state["next_question"]

print("Workflow started:", datetime.now(timezone.utc))
print("Question index:", index)

# Get today's question
question = questions[index]

# Telegram API URL
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Send the message
response = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": f"❤️ A little question for us today:\n\n{question}"
    }
)

# Stop if Telegram returned an error
response.raise_for_status()

print("Question sent successfully.")

# Update state
state["last_question"] = question
state["last_sent"] = datetime.now().strftime("%Y-%m-%d")
state["next_question"] = (index + 1) % len(questions)

# Save updated state
with open("state.json", "w") as f:
    json.dump(state, f, indent=2)

print("State updated.")
