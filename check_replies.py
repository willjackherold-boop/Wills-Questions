import json
import os
import requests

TOKEN = os.environ["BOT_TOKEN"]

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

response = requests.get(url)

print("Status:", response.status_code)
print(json.dumps(response.json(), indent=4))
