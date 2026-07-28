import csv
import json
import os
import random
import requests

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

with open("questions.csv") as f:
    reader = csv.DictReader(f)
    questions = [row["Question"] for row in reader]

question = random.choice(questions)

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(url, json={
    "chat_id": CHAT_ID,
    "text": "❤️ Today's question:\n\n" + question
