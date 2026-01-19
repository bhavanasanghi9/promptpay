import requests

print("=" * 60)
print("🧪 Testing Local Server Headers")
print("=" * 60)
print()

# Test your ngrok endpoint
url = "https://alondra-lyriform-gwenn.ngrok-free.dev/prompt"

payload = {"prompt": "Test payment headers"}

print(f"📡 Sending request to: {url}")
print(f"📦 Payload: {payload}")
print()

try:
    response = requests.post(url, json=payload, timeout=10)
    
    print(f"📊 Status Code: {response.status_code}")
    print()
    
    print("📋 Response Headers:")
    print("-" * 60)
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    print("-" * 60)
    print()
    
    # Check for x402 payment headers
    if "X-Accept-Payment" in response.headers:
        print("✅ Found X-Accept-Payment header!")
        print(f"   Value: {response.headers['X-Accept-Payment']}")
    else:
        print("❌ X-Accept-Payment header NOT found!")
        print()
        print("⚠️  This is the problem! thirdweb needs this header.")
    
    print()
    print("📄 Response Body:")
    print("-" * 60)
    print(response.text)
    print("-" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)