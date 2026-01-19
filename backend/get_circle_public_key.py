import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CIRCLE_W3S_API_KEY")

if not API_KEY:
    print("❌ Missing CIRCLE_W3S_API_KEY")
    exit(1)

url = "https://api.circle.com/v1/w3s/config/entity/publicKey"

headers = {
    "accept": "application/json",
    "authorization": f"Bearer {API_KEY}",
}

print("🔐 Fetching Circle entity public key...\n")

response = requests.get(url, headers=headers, timeout=10)

print(f"Status Code: {response.status_code}\n")
print("Raw Response:\n")
print(response.text)
