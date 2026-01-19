from thirdweb import ThirdwebSDK
import os
import json

# ⚠️ Test wallet private key (NEVER use real funds)
PAYER_PRIVATE_KEY = os.getenv("TEST_PAYER_PRIVATE_KEY")

AGENT_WALLET_ADDRESS = os.getenv("AGENT_WALLET_ADDRESS")
AMOUNT_USDC = "0.001"
CHAIN = "arc-testnet"

if not PAYER_PRIVATE_KEY:
    raise RuntimeError("Missing TEST_PAYER_PRIVATE_KEY")

sdk = ThirdwebSDK(CHAIN, private_key=PAYER_PRIVATE_KEY)

# This creates a signed payment proof (x402-style)
payment_proof = sdk.payments.create_payment_proof(
    recipient=AGENT_WALLET_ADDRESS,
    amount=AMOUNT_USDC,
    currency="USDC",
)

print("\n✅ x402 PAYMENT PROOF:\n")
print(payment_proof)
print("\n(copy this entire string into X-PAYMENT header)")
