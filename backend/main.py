from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from decimal import Decimal

from dotenv import load_dotenv
import google.generativeai as genai

from blockchain_verifier import ArcPaymentVerifier
from payment_ledger import PaymentLedger

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

AGENT_WALLET_ADDRESS = os.getenv("AGENT_WALLET_ADDRESS")
EXPECTED_PAYMENT_USDC = os.getenv("EXPECTED_PAYMENT_USDC", "0.001")

# NEW: confirmations required (must match blockchain_verifier default)
MIN_CONFIRMATIONS = int(os.getenv("MIN_CONFIRMATIONS", "2"))

if not AGENT_WALLET_ADDRESS:
    raise RuntimeError("Missing AGENT_WALLET_ADDRESS in .env")

# -------------------------------------------------
# Gemini setup
# -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# -------------------------------------------------
# Initialize blockchain verifier and ledger (ONCE)
# -------------------------------------------------
verifier = ArcPaymentVerifier()
ledger = PaymentLedger()

# -------------------------------------------------
# Pricing function (foundation for dynamic pricing)
# -------------------------------------------------
def calculate_price(prompt: str) -> Decimal:
    """
    Calculate price for a prompt.
    Currently flat rate, but ready for dynamic pricing.
    """
    return Decimal(EXPECTED_PAYMENT_USDC)

# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI(
    title="Pay-per-Prompt AI Agent",
    description="AI agent with on-chain payment verification on Arc",
    version="1.0.0"
)

# ✅ CORS FIX (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Request model
# -------------------------------------------------
class PromptRequest(BaseModel):
    prompt: str

# -------------------------------------------------
# Main endpoint with LEDGER INTEGRATION
# -------------------------------------------------
@app.post("/prompt")
def prompt(
    req: PromptRequest,
    x_payment: str | None = Header(default=None, alias="X-Payment"),
):
    """
    Pay-per-prompt AI agent with:
    - Real Arc blockchain verification
    - Transaction reuse prevention
    - Credit tracking
    - Overpayment handling
    - NEW: confirmation handling
    - NEW: underpayment handling (vs calculated price)
    """

    price = calculate_price(req.prompt)

    # 1️⃣ No payment → return 402 with instructions
    if not x_payment:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Payment required",
                "agent": "pay-per-prompt-ai",
                "payment": {
                    "amount": str(price),
                    "currency": "USDC",
                    "chain": "ARC-TESTNET",
                    "chain_id": 5042002,
                    "recipient": AGENT_WALLET_ADDRESS,
                    "retry_header": "X-Payment",
                },
                "message": (
                    f"Send {price} USDC to {AGENT_WALLET_ADDRESS} on Arc testnet "
                    "and retry with the transaction hash in X-Payment header"
                ),
            },
        )

    # 2️⃣ Check if transaction was already used (REUSE PREVENTION)
    if ledger.has_transaction(x_payment):
        record = ledger.get(x_payment)

        if record["remaining"] >= float(price):
            try:
                ledger.consume(x_payment, float(price))
                response = model.generate_content(req.prompt)
                updated_record = ledger.get(x_payment)

                return {
                    "answer": response.text,
                    "receipt": {
                        "payment_type": "credit",
                        "amount_consumed": str(price),
                        "remaining_credit": str(updated_record["remaining"]),
                        "tx_hash": x_payment,
                        "original_payment": str(record["total_paid"]),
                    },
                    "status": "paid_with_credit",
                }
            except ValueError as e:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Credit consumption failed",
                        "reason": str(e),
                    }
                )
        else:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Transaction already used and no credit remaining",
                    "tx_hash": x_payment,
                    "remaining_credit": str(record["remaining"]),
                    "required": str(price),
                    "message": "Please make a new payment",
                },
            )

    # 3️⃣ New transaction → verify on-chain (recipient, status, amount, confirmations)
    verification = verifier.verify_payment_tx(x_payment)

    if not verification.get("valid"):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Payment verification failed",
                "reason": verification.get("error"),
                "agent": "pay-per-prompt-ai",
                "required_amount": str(price),
            },
        )

    # 3.5️⃣ NEW: confirmation handling
    confirmations = int(verification.get("confirmations", 0))
    if confirmations < MIN_CONFIRMATIONS:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Payment not confirmed enough yet",
                "tx_hash": x_payment,
                "confirmations": confirmations,
                "min_confirmations": MIN_CONFIRMATIONS,
                "message": "Wait a few seconds and retry with the same tx hash.",
            },
        )

    # 3.6️⃣ NEW: underpayment handling vs the *actual price*
    paid = Decimal(verification["amount_usdc"])
    if paid < price:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Underpayment",
                "tx_hash": x_payment,
                "paid": str(paid),
                "required": str(price),
                "shortfall": str(price - paid),
                "message": "Please send the shortfall in a new transaction.",
            },
        )

    # 4️⃣ Record payment in ledger
    try:
        ledger.record_payment(
            tx_hash=x_payment,
            from_addr=verification["from"],
            to_addr=verification["to"],
            amount=float(paid),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Ledger error",
                "reason": str(e)
            }
        )

    # 5️⃣ Consume the required amount (will leave remaining as credit)
    try:
        ledger.consume(x_payment, float(price))
    except ValueError as e:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Insufficient payment",
                "reason": str(e),
                "paid": str(paid),
                "required": str(price),
            }
        )

    # 6️⃣ Run AI
    response = model.generate_content(req.prompt)

    # 7️⃣ Receipt
    final_record = ledger.get(x_payment)

    return {
        "answer": response.text,
        "receipt": {
            "payment_type": "new_payment",
            "amount_paid": str(paid),
            "amount_consumed": str(price),
            "remaining_credit": str(final_record["remaining"]),
            "tx_hash": verification["tx_hash"],
            "from_address": verification["from"],
            "to_address": verification["to"],
            "block_number": verification["block"],
            "confirmations": confirmations,
            "min_confirmations": MIN_CONFIRMATIONS,
        },
        "status": "paid_and_verified",
    }

# -------------------------------------------------
# Additional endpoints
# -------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "operational",
        "service": "Pay-per-Prompt AI Agent",
        "features": [
            "On-chain payment verification",
            "Transaction reuse prevention",
            "Credit tracking",
            "Overpayment handling",
            "Confirmation handling",
            "Underpayment handling"
        ],
        "price_per_prompt": str(EXPECTED_PAYMENT_USDC),
        "currency": "USDC",
        "chain": "Arc Testnet",
        "agent_wallet": AGENT_WALLET_ADDRESS,
        "min_confirmations": MIN_CONFIRMATIONS,
    }

@app.get("/stats")
def stats():
    all_payments = ledger.all_payments()

    total_received = sum(p["total_paid"] for p in all_payments)
    total_consumed = sum(p["consumed"] for p in all_payments)
    total_remaining = sum(p["remaining"] for p in all_payments)

    return {
        "total_payments": len(all_payments),
        "total_received_usdc": str(total_received),
        "total_consumed_usdc": str(total_consumed),
        "total_remaining_credits": str(total_remaining),
        "agent_wallet": AGENT_WALLET_ADDRESS,
    }

@app.get("/payment/{tx_hash}")
def get_payment_info(tx_hash: str):
    record = ledger.get(tx_hash)

    if not record:
        raise HTTPException(
            status_code=404,
            detail={"error": "Payment not found"}
        )

    return record

# -------------------------------------------------
# Dashboard / Analytics Endpoints
# -------------------------------------------------

@app.get("/payments")
def list_payments():
    """
    List all payment transactions.
    Used for frontend tables / dashboards.
    """
    return {
        "count": len(ledger.all_payments()),
        "payments": ledger.all_payments(),
    }


@app.get("/revenue")
def revenue():
    """
    Revenue and business metrics.
    Judges LOVE this.
    """
    return {
        "total_revenue_usdc": ledger.total_revenue(),
        "total_consumed_usdc": ledger.total_consumed(),
        "total_remaining_credits": ledger.total_remaining(),
        "total_prompts_served": ledger.total_prompts_served(),
        "price_per_prompt": EXPECTED_PAYMENT_USDC,
        "agent_wallet": AGENT_WALLET_ADDRESS,
    }


@app.get("/usage")
def usage():
    """
    Per-transaction usage breakdown.
    """
    data = []
    for p in ledger.all_payments():
        data.append({
            "tx_hash": p["tx_hash"],
            "from": p["from"],
            "total_paid": p["total_paid"],
            "consumed": p["consumed"],
            "remaining": p["remaining"],
            "prompts_served": p["uses"],
        })

    return {
        "transactions": data
    }
