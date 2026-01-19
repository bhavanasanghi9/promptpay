import os
import uuid
import base64
import requests
from dotenv import load_dotenv

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# ========================================
# STEP 1: Load environment variables
# ========================================
load_dotenv()

# ========================================
# STEP 2: Read required env vars
# ========================================
API_KEY = os.getenv("CIRCLE_W3S_API_KEY")
ENTITY_SECRET_HEX = os.getenv("CIRCLE_ENTITY_SECRET_HEX")

if not API_KEY:
    print("❌ ERROR: Missing CIRCLE_W3S_API_KEY in .env file")
    exit(1)

if not ENTITY_SECRET_HEX:
    print("❌ ERROR: Missing CIRCLE_ENTITY_SECRET_HEX in .env file")
    exit(1)

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {API_KEY}",
}

print("=" * 60)
print("🏦 Creating AI Agent Wallet on Arc Testnet")
print("=" * 60)
print()

# ========================================
# STEP 3: Entity secret encryption helpers
# ========================================

def get_entity_public_key_pem() -> str:
    """Fetch Circle's entity public key (their 'lock')."""
    url = "https://api.circle.com/v1/w3s/config/entity/publicKey"
    resp = requests.get(url, headers=headers, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch entity public key: {resp.status_code} {resp.text}"
        )

    return resp.json()["data"]["publicKey"]


def generate_entity_secret_ciphertext() -> str:
    """
    Encrypt OUR entity secret using Circle's public key.
    This proves we own the app without revealing the secret.
    """
    public_key_pem = get_entity_public_key_pem().encode("utf-8")
    public_key = serialization.load_pem_public_key(public_key_pem)

    secret_bytes = bytes.fromhex(ENTITY_SECRET_HEX)

    ciphertext = public_key.encrypt(
        secret_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return base64.b64encode(ciphertext).decode("utf-8")


# ========================================
# STEP 4: Create Wallet Set
# ========================================
print("📦 Step 1: Creating Wallet Set...\n")

wallet_set_url = "https://api.circle.com/v1/w3s/developer/walletSets"

wallet_set_payload = {
    "idempotencyKey": str(uuid.uuid4()),
    "name": "AI Agent Wallet Set",
    "entitySecretCiphertext": generate_entity_secret_ciphertext(),
}

ws_response = requests.post(
    wallet_set_url, json=wallet_set_payload, headers=headers, timeout=15
)

print(f"📊 Wallet Set Status: {ws_response.status_code}")

if ws_response.status_code != 201:
    print("❌ Wallet Set creation failed")
    print(ws_response.text)
    exit(1)

wallet_set_id = ws_response.json()["data"]["walletSet"]["id"]

print("✅ Wallet Set Created")
print(f"🆔 Wallet Set ID: {wallet_set_id}\n")

# ========================================
# STEP 5: Create Wallet
# ========================================
print("💼 Step 2: Creating Wallet...\n")

wallet_url = "https://api.circle.com/v1/w3s/developer/wallets"

wallet_payload = {
    "idempotencyKey": str(uuid.uuid4()),
    "walletSetId": wallet_set_id,
    "blockchains": ["ARC-TESTNET"],
    "count": 1,
    "entitySecretCiphertext": generate_entity_secret_ciphertext(),
    "metadata": [
    {
        "name": "purpose",
        "value": "ai-prompt-agent"
    }
],
}

w_response = requests.post(
    wallet_url, json=wallet_payload, headers=headers, timeout=15
)

print(f"📊 Wallet Status: {w_response.status_code}")
print("-" * 60)

if w_response.status_code != 201:
    print("❌ Wallet creation failed")
    print(w_response.text)
    exit(1)

wallet = w_response.json()["data"]["wallets"][0]

wallet_id = wallet["id"]
wallet_address = wallet["address"]
blockchain = wallet["blockchain"]

print("✅ SUCCESS! Agent wallet created!\n")
print("📋 Wallet Details")
print("-" * 60)
print(f"🆔 Wallet ID: {wallet_id}")
print(f"📍 Wallet Address: {wallet_address}")
print(f"⛓️  Blockchain: {blockchain}")
print(f"🆔 Wallet Set ID: {wallet_set_id}\n")

print("⚠️  ADD THESE TO YOUR .env FILE")
print("=" * 60)
print(f"AGENT_WALLET_ID={wallet_id}")
print(f"AGENT_WALLET_ADDRESS={wallet_address}")
print(f"AGENT_WALLET_SET_ID={wallet_set_id}")
print("=" * 60)

print("\n💡 Your AI agent will receive USDC at:")
print(wallet_address)
print("\n🎉 Done.")
