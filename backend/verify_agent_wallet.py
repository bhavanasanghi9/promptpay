import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Get credentials from .env
CIRCLE_API_KEY = os.getenv("CIRCLE_W3S_API_KEY")
AGENT_WALLET_ID = os.getenv("AGENT_WALLET_ID")
AGENT_WALLET_ADDRESS = os.getenv("AGENT_WALLET_ADDRESS")
AGENT_WALLET_SET_ID = os.getenv("AGENT_WALLET_SET_ID")

print("=" * 60)
print("🔍 Verifying Agent Wallet Configuration")
print("=" * 60)
print()

# Check all required variables
if not CIRCLE_API_KEY:
    print("❌ Missing CIRCLE_W3S_API_KEY")
    exit(1)

if not AGENT_WALLET_ID:
    print("❌ Missing AGENT_WALLET_ID")
    exit(1)

if not AGENT_WALLET_ADDRESS:
    print("❌ Missing AGENT_WALLET_ADDRESS")
    exit(1)

print("✅ All wallet variables found in .env")
print()
print(f"🆔 Wallet ID: {AGENT_WALLET_ID}")
print(f"📍 Wallet Address: {AGENT_WALLET_ADDRESS}")
print(f"🗂️  Wallet Set ID: {AGENT_WALLET_SET_ID}")
print()

# Test 1: Get wallet details from Circle API
print("📡 Test 1: Fetching wallet details from Circle...")
print("-" * 60)

url = f"https://api.circle.com/v1/w3s/wallets/{AGENT_WALLET_ID}"
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {CIRCLE_API_KEY}",
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Wallet found!")
        data = response.json()
        wallet = data.get("data", {}).get("wallet", {})
        
        print()
        print("📋 Wallet Details:")
        print(f"  Address: {wallet.get('address')}")
        print(f"  Blockchain: {wallet.get('blockchain')}")
        print(f"  State: {wallet.get('state')}")
        print(f"  Created: {wallet.get('createDate')}")
        print(f"  Updated: {wallet.get('updateDate')}")
        
        # Verify address matches
        if wallet.get('address') == AGENT_WALLET_ADDRESS:
            print()
            print("✅ Address matches .env configuration!")
        else:
            print()
            print("⚠️  Warning: Address doesn't match .env")
            print(f"  .env has: {AGENT_WALLET_ADDRESS}")
            print(f"  API returned: {wallet.get('address')}")
        
        # Check if it's on Arc
        blockchain = wallet.get('blockchain', '').lower()
        if 'arc' in blockchain:
            print("✅ Wallet is on Arc network!")
        else:
            print(f"⚠️  Warning: Wallet blockchain is '{blockchain}', expected Arc")
            
    elif response.status_code == 404:
        print("❌ Wallet not found!")
        print("Your AGENT_WALLET_ID might be incorrect.")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 60)

# Test 2: Check wallet balance
print()
print("📡 Test 2: Checking wallet balance...")
print("-" * 60)

balance_url = f"https://api.circle.com/v1/w3s/wallets/{AGENT_WALLET_ID}/balances"

try:
    response = requests.get(balance_url, headers=headers, timeout=10)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        balances = data.get("data", {}).get("tokenBalances", [])
        
        if balances:
            print("✅ Balance information:")
            print()
            for balance in balances:
                token = balance.get("token", {})
                amount = balance.get("amount", "0")
                print(f"  💰 {token.get('symbol', 'Unknown')}: {amount}")
        else:
            print("ℹ️  Wallet has 0 balance (expected for new wallet)")
            print()
            print("💡 To test payments, you'll need to:")
            print("   1. Get Arc testnet USDC")
            print("   2. Send it to this wallet")
    else:
        print(f"⚠️  Could not fetch balance: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 60)
print("✅ Wallet verification complete!")
print("=" * 60)
print()
print("📝 Next Steps:")
print("1. If wallet is verified, we'll add on-chain payment verification")
print("2. We'll check Arc blockchain for incoming USDC transactions")
print("3. We'll integrate this into your AI agent")