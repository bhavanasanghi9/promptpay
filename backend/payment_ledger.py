# """
# In-memory Payment Ledger
# Tracks payments, usage, and remaining credit
# """

# import time

# class PaymentLedger:
#     def __init__(self):
#         # tx_hash -> payment record
#         self._ledger = {}

#     def has_transaction(self, tx_hash: str) -> bool:
#         return tx_hash in self._ledger

#     def record_payment(self, tx_hash: str, from_addr: str, to_addr: str, amount: float):
#         if tx_hash in self._ledger:
#             raise ValueError("Transaction already recorded")

#         self._ledger[tx_hash] = {
#             "tx_hash": tx_hash,
#             "from": from_addr,
#             "to": to_addr,
#             "total_paid": amount,
#             "consumed": 0.0,
#             "remaining": amount,
#             "timestamp": int(time.time())
#         }

#     def consume(self, tx_hash: str, amount: float):
#         if tx_hash not in self._ledger:
#             raise ValueError("Unknown transaction")

#         record = self._ledger[tx_hash]

#         if record["remaining"] < amount:
#             raise ValueError("Insufficient remaining credit")

#         record["consumed"] += amount
#         record["remaining"] -= amount

#     def get(self, tx_hash: str) -> dict:
#         return self._ledger.get(tx_hash)

#     def all_payments(self):
#         return list(self._ledger.values())


from typing import Dict, List
import time


class PaymentLedger:
    """
    In-memory ledger for payment tracking.
    Safe for hackathons / demos / MVPs.
    """

    def __init__(self):
        self._ledger: Dict[str, dict] = {}

    # -----------------------------
    # Core operations
    # -----------------------------
    def record_payment(self, tx_hash: str, from_addr: str, to_addr: str, amount: float):
        if tx_hash in self._ledger:
            raise ValueError("Transaction already recorded")

        self._ledger[tx_hash] = {
            "tx_hash": tx_hash,
            "from": from_addr,
            "to": to_addr,
            "total_paid": amount,
            "consumed": 0.0,
            "remaining": amount,
            "created_at": time.time(),
            "uses": 0,
        }

    def consume(self, tx_hash: str, amount: float):
        if tx_hash not in self._ledger:
            raise ValueError("Transaction not found")

        record = self._ledger[tx_hash]

        if record["remaining"] < amount:
            raise ValueError("Insufficient credit")

        record["remaining"] -= amount
        record["consumed"] += amount
        record["uses"] += 1

    # -----------------------------
    # Read helpers
    # -----------------------------
    def has_transaction(self, tx_hash: str) -> bool:
        return tx_hash in self._ledger

    def get(self, tx_hash: str):
        return self._ledger.get(tx_hash)

    def all_payments(self) -> List[dict]:
        return list(self._ledger.values())

    # -----------------------------
    # Stats helpers
    # -----------------------------
    def total_revenue(self) -> float:
        return sum(p["total_paid"] for p in self._ledger.values())

    def total_consumed(self) -> float:
        return sum(p["consumed"] for p in self._ledger.values())

    def total_remaining(self) -> float:
        return sum(p["remaining"] for p in self._ledger.values())

    def total_prompts_served(self) -> int:
        return sum(p["uses"] for p in self._ledger.values())
