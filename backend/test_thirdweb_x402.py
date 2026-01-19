import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get thirdweb secret key
THIRDWEB_SECRET_KEY = os.getenv("THIRDWEB_SECRET_KEY")

if not THIRDWEB_SECRET_KEY:
    print("❌ Missing THIRDWEB_SECRET_KEY in .env")
    exit(1)

print("=" * 60)
print("🧪 Testing thirdweb x402 Facilitator")
print("=" * 60)
print()
print(f"🔑 Secret Key: {THIRDWEB_SECRET_KEY[:15]}...")
print()

# Your ngrok URL (the AI agent endpoint)
agent_url = "https://alondra-lyriform-gwenn.ngrok-free.dev/prompt"

# thirdweb x402 facilitator endpoint
facilitator_url = f"https://api.thirdweb.com/v1/payments/x402/fetch?url={agent_url}&method=POST&maxValue=10000"

# Headers
headers = {
    "x-secret-key": THIRDWEB_SECRET_KEY,
    "Content-Type": "application/json"
}

# Payload to send to your AI agent
payload = {
    "prompt": "Explain quantum computing in simple terms"
}

print("📡 Sending request to thirdweb x402 facilitator...")
print(f"🌐 Agent URL: {agent_url}")
print(f"💰 Max Value: 10000 wei")
print(f"📦 Payload: {payload}")
print()

try:
    response = requests.post(
        facilitator_url,
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"📊 Status Code: {response.status_code}")
    print("-" * 60)
    
    if response.status_code == 200:
        print("✅ SUCCESS! Payment processed and AI responded!")
        print()
        print("📄 Response:")
        data = response.json()
        print(data)
        
        # Show AI answer if present
        if "answer" in data:
            print()
            print("🤖 AI Answer:")
            print("-" * 60)
            print(data["answer"])
            print("-" * 60)
        
    elif response.status_code == 400:
        print("❌ BAD REQUEST")
        print()
        data = response.json()
        print(f"Error: {data.get('error')}")
        print(f"Message: {data.get('message')}")
        print()
        print("💡 Common issues:")
        print("   - Check X-Accept-Payment header format")
        print("   - Ensure chain ID is correct (eip155:5042002)")
        print("   - Verify agent URL is accessible")
        
    elif response.status_code == 401:
        print("❌ UNAUTHORIZED!")
        print()
        print("Your thirdweb secret key is invalid.")
        print()
        print("💡 Check your .env file:")
        print("   THIRDWEB_SECRET_KEY=sk_...")
        
    elif response.status_code == 402:
        print("💰 PAYMENT REQUIRED!")
        print()
        print("This means thirdweb is trying to handle payment.")
        print()
        data = response.json()
        print("📄 Payment Details:")
        print(data)
        
    elif response.status_code == 500:
        print("❌ SERVER ERROR")
        print()
        print("thirdweb or your agent had an internal error.")
        print()
        print(f"📄 Response: {response.text}")
        
    else:
        print(f"⚠️  Unexpected Status: {response.status_code}")
        print()
        print("📄 Full Response:")
        print(response.text)
    
    # Show all response headers
    print()
    print("📋 Response Headers:")
    print("-" * 60)
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    print("-" * 60)
        
except requests.exceptions.Timeout:
    print("❌ TIMEOUT!")
    print("The request took too long (>30 seconds).")
    print()
    print("💡 Possible causes:")
    print("   - Your agent is slow to respond")
    print("   - Network issues")
    print("   - Payment processing taking too long")
    
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR!")
    print("Could not connect to thirdweb API.")
    print()
    print("💡 Check:")
    print("   - Your internet connection")
    print("   - thirdweb API status")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Test Complete!")
print("=" * 60)