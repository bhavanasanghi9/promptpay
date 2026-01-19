import os
import requests
from dotenv import load_dotenv

# ========================================
# STEP 1: Load environment variables
# ========================================
load_dotenv()

# ========================================
# STEP 2: Get Circle API key from .env
# ========================================
API_KEY = os.getenv("CIRCLE_W3S_API_KEY")

# Check if API key exists
if not API_KEY:
    print("❌ ERROR: Missing CIRCLE_W3S_API_KEY in .env file")
    print("💡 Make sure you have a line like:")
    print("   CIRCLE_W3S_API_KEY=your_key_here")
    exit(1)

print("=" * 50)
print("🔍 Testing Circle API Connection")
print("=" * 50)
print(f"🔑 API Key found: {API_KEY[:15]}...")
print()

# ========================================
# STEP 3: Set up API request
# ========================================
# Circle API endpoint to list wallets
url = "https://api.circle.com/v1/w3s/wallets"

# Request headers (how we authenticate)
headers = {
    "accept": "application/json",
    "authorization": f"Bearer {API_KEY}",  # This is how Circle knows it's you
}

# ========================================
# STEP 4: Make the API call
# ========================================
print("📡 Sending request to Circle API...")
print(f"🌐 URL: {url}")
print()

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    # ========================================
    # STEP 5: Check the response
    # ========================================
    print(f"📊 Response Status: {response.status_code}")
    print("-" * 50)
    
    if response.status_code == 200:
        # SUCCESS! API key works
        print("✅ SUCCESS! Your Circle API key is VALID!")
        print()
        
        # Parse the response
        data = response.json()
        wallets = data.get("data", {}).get("wallets", [])
        
        print(f"💼 You have {len(wallets)} wallet(s) in your account")
        print()
        
        if wallets:
            print("📋 Your existing wallets:")
            print("-" * 50)
            for i, wallet in enumerate(wallets, 1):
                print(f"\n  Wallet #{i}")
                print(f"  🆔 ID: {wallet.get('id')}")
                print(f"  ⛓️  Blockchain: {wallet.get('blockchain')}")
                print(f"  📍 Address: {wallet.get('address')}")
                print(f"  📅 Created: {wallet.get('createDate', 'N/A')}")
        else:
            print("ℹ️  No wallets found yet. We'll create one in the next step!")
            
    elif response.status_code == 401:
        # UNAUTHORIZED - API key is wrong
        print("❌ AUTHENTICATION FAILED!")
        print()
        print("Your API key is invalid or expired.")
        print()
        print("💡 Please check:")
        print("   1. Copy the FULL API key from Circle console")
        print("   2. Make sure there are no extra spaces")
        print("   3. The key should look like: TEST_API_KEY:...")
        print()
        print(f"📄 Raw response: {response.text}")
        
    elif response.status_code == 403:
        # FORBIDDEN - API key doesn't have permission
        print("❌ PERMISSION DENIED!")
        print()
        print("Your API key doesn't have permission to access wallets.")
        print()
        print(f"📄 Raw response: {response.text}")
        
    else:
        # OTHER ERROR
        print(f"⚠️  Unexpected response code: {response.status_code}")
        print()
        print(f"📄 Raw response: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ REQUEST TIMEOUT!")
    print("The API request took too long. Check your internet connection.")
    
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR!")
    print("Could not connect to Circle API. Check your internet connection.")
    
except Exception as e:
    print(f"❌ UNEXPECTED ERROR!")
    print(f"Error: {str(e)}")

print()
print("=" * 50)
print("Test complete!")
print("=" * 50)