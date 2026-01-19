import os
import base64
import requests
from dotenv import load_dotenv

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

load_dotenv()

API_KEY = os.getenv("CIRCLE_W3S_API_KEY")
ENTITY_SECRET_HEX = os.getenv("CIRCLE_ENTITY_SECRET_HEX")

if not API_KEY or not ENTITY_SECRET_HEX:
    print("❌ Missing env vars")
    exit(1)

# 1️⃣ Fetch Circle public key
url = "https://api.circle.com/v1/w3s/config/entity/publicKey"
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {API_KEY}",
}

response = requests.get(url, headers=headers, timeout=10)
public_key_pem = response.json()["data"]["publicKey"]

print("🔓 Circle Public Key loaded")

# 2️⃣ Load public key
public_key = serialization.load_pem_public_key(
    public_key_pem.encode("utf-8")
)

# 3️⃣ Encrypt YOUR secret using Circle's key
secret_bytes = bytes.fromhex(ENTITY_SECRET_HEX)

ciphertext = public_key.encrypt(
    secret_bytes,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    ),
)

ciphertext_b64 = base64.b64encode(ciphertext).decode("utf-8")

print("\n✅ entitySecretCiphertext generated:\n")
print(ciphertext_b64)
print("\n(length:", len(ciphertext_b64), "chars )")
