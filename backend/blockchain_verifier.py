"""
Arc Native USDC Payment Verifier
Correct verification for Arc where USDC is the native currency
Adds block-confirmation support (safety)
"""

import os
import sys
from decimal import Decimal
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# Arc configuration
# ---------------------------
ARC_TESTNET_RPC = "https://rpc.testnet.arc.network"
ARC_TESTNET_CHAIN_ID = 5042002

# Native USDC on Arc uses 18 decimals (as you already observed working)
USDC_DECIMALS = 18

AGENT_WALLET_ADDRESS = os.getenv("AGENT_WALLET_ADDRESS")
EXPECTED_PAYMENT_USDC = Decimal(os.getenv("EXPECTED_PAYMENT_USDC", "0.001"))

# NEW: confirmations requirement (can override from .env)
MIN_CONFIRMATIONS = int(os.getenv("MIN_CONFIRMATIONS", "2"))

if not AGENT_WALLET_ADDRESS:
    raise RuntimeError("Missing AGENT_WALLET_ADDRESS in .env")

AGENT_WALLET_ADDRESS = Web3.to_checksum_address(AGENT_WALLET_ADDRESS)


class ArcPaymentVerifier:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(ARC_TESTNET_RPC))

        if not self.w3.is_connected():
            raise ConnectionError("Could not connect to Arc testnet RPC")

        chain_id = self.w3.eth.chain_id
        if chain_id != ARC_TESTNET_CHAIN_ID:
            raise RuntimeError(f"Wrong chain: {chain_id}")

        print(f"✅ Connected to Arc Testnet (Chain ID: {chain_id})")

    def usdc_to_wei(self, usdc: Decimal) -> int:
        return int(usdc * (10 ** USDC_DECIMALS))

    def wei_to_usdc(self, wei: int) -> Decimal:
        return Decimal(wei) / (10 ** USDC_DECIMALS)

    def get_wallet_balance(self, address: str) -> Decimal:
        wei_balance = self.w3.eth.get_balance(Web3.to_checksum_address(address))
        return self.wei_to_usdc(wei_balance)

    def verify_payment_tx(self, tx_hash: str) -> dict:
        """
        Verifies:
          - tx exists
          - succeeded
          - correct recipient
          - returns amount + confirmations

        Does NOT enforce pricing/underpayment here, because pricing belongs in main.py.
        """
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash

        print(f"🔍 Verifying tx: {tx_hash}")

        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            return {"valid": False, "error": f"RPC error: {e}"}

        if receipt is None or tx is None:
            return {"valid": False, "error": "Transaction not found"}

        if receipt.status != 1:
            return {"valid": False, "error": "Transaction failed"}

        if tx["to"] is None:
            return {"valid": False, "error": "No recipient address"}

        if Web3.to_checksum_address(tx["to"]) != AGENT_WALLET_ADDRESS:
            return {
                "valid": False,
                "error": f"Wrong recipient. Expected {AGENT_WALLET_ADDRESS}, got {tx['to']}",
            }

        # Amount sent (native value) -> USDC
        amount_usdc = self.wei_to_usdc(tx["value"])

        # NEW: confirmations
        try:
            latest_block = self.w3.eth.block_number
            confirmations = int(latest_block - receipt.blockNumber)
        except Exception as e:
            return {"valid": False, "error": f"Could not compute confirmations: {e}"}

        return {
            "valid": True,
            "tx_hash": tx_hash,
            "from": tx["from"],
            "to": tx["to"],
            "amount_usdc": str(amount_usdc),
            "block": receipt.blockNumber,
            "confirmations": confirmations,
            "min_confirmations": MIN_CONFIRMATIONS,
        }


def main():
    print("=" * 60)
    print("🧪 Arc Native USDC Payment Verifier")
    print("=" * 60)

    verifier = ArcPaymentVerifier()

    print()
    print(f"📍 Agent Wallet: {AGENT_WALLET_ADDRESS}")
    balance = verifier.get_wallet_balance(AGENT_WALLET_ADDRESS)
    print(f"💰 Agent Balance: {balance} USDC")
    print(f"🧱 MIN_CONFIRMATIONS: {MIN_CONFIRMATIONS}")

    if len(sys.argv) > 1:
        print()
        result = verifier.verify_payment_tx(sys.argv[1])
        print("✅ Verification Result:")
        print(result)
    else:
        print()
        print("Run:")
        print("  python blockchain_verifier.py <tx_hash>")


if __name__ == "__main__":
    main()
