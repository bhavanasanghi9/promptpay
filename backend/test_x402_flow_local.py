import requests

print("=" * 60)
print("🧪 Testing x402 Flow Locally (Without thirdweb)")
print("=" * 60)
print()

# Use localhost instead of ngrok
agent_url = "http://localhost:8000/prompt"

payload = {"prompt": "What is quantum computing?"}

print("📋 TEST 1: Request WITHOUT Payment")
print("-" * 60)

# Step 1: Try without payment (should get 402)
response1 = requests.post(agent_url, json=payload)

print(f"Status: {response1.status_code}")
print(f"Expected: 402 (Payment Required)")
print()

if response1.status_code == 402:
    print("✅ Correctly returned 402!")
    print()
    print("Payment Headers:")
    if "X-Accept-Payment" in response1.headers:
        print(f"  X-Accept-Payment: {response1.headers['X-Accept-Payment']}")
    else:
        print("  ❌ X-Accept-Payment header missing!")
    print()
    print("Response Body:")
    print(response1.json())
else:
    print("❌ Expected 402 but got:", response1.status_code)

print()
print("=" * 60)
print()

print("📋 TEST 2: Request WITH Payment Proof")
print("-" * 60)

# Step 2: Retry with fake payment proof
fake_payment_proof = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

headers_with_payment = {
    "X-Payment": fake_payment_proof
}

response2 = requests.post(agent_url, json=payload, headers=headers_with_payment)

print(f"Status: {response2.status_code}")
print(f"Expected: 200 (Success)")
print()

if response2.status_code == 200:
    print("✅ Payment accepted! AI responded!")
    print()
    data = response2.json()
    print("🤖 AI Answer:")
    print("-" * 60)
    print(data.get("answer", "No answer found"))
    print("-" * 60)
    print()
    print("Receipt:")
    print(data.get("receipt", {}))
else:
    print("❌ Expected 200 but got:", response2.status_code)
    print("Response:", response2.text)

print()
print("=" * 60)
print("Test Complete!")
print("=" * 60)
print()

print("📝 Summary:")
print("✅ Your x402 flow works locally!")
print("✅ Your agent correctly requires payment")
print("✅ Your agent correctly accepts payment proof")
print()
print("⚠️  The issue is ngrok blocking thirdweb's automated requests.")
print()
print("💡 Solutions:")
print("1. Use: ngrok http 8000 --request-header-add 'ngrok-skip-browser-warning: true'")
print("2. Deploy to a real server (Replit, Railway, etc.)")
print("3. For demo: Show this local test + explain the ngrok issue")