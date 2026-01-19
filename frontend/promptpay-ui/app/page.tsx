"use client";

import { useEffect, useMemo, useState } from "react";
import { PaymentRequiredDetail, postPrompt, sleep } from "@/lib/api";

/* -------------------------------------------------
   Client-side analytics logging
------------------------------------------------- */
function logPromptEvent(txHash?: string) {
  try {
    const key = "prompt_events";
    const raw = localStorage.getItem(key);
    const events = raw ? JSON.parse(raw) : [];

    events.push({
      ts: Date.now(),
      tx_hash: txHash ?? null,
    });

    localStorage.setItem(key, JSON.stringify(events));
  } catch {
    // analytics must never break UX
  }
}

/* -------------------------------------------------
   Wallet state (backend-verified)
------------------------------------------------- */
type WalletState =
  | { status: "none" }
  | { status: "pending"; confirmations: number; min: number }
  | { status: "active"; remaining: number; total: number }
  | { status: "empty" }
  | { status: "invalid" };

export default function PromptPage() {
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [paymentDetail, setPaymentDetail] =
    useState<PaymentRequiredDetail | null>(null);

  const [txHash, setTxHash] = useState("");
  const [walletState, setWalletState] = useState<WalletState>({
    status: "none",
  });

  const priceLabel = useMemo(() => "0.001 USDC", []);

  /* -------------------------------------------------
     Session helpers
  ------------------------------------------------- */
  function getSessionTx() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("paymentTxHash");
  }

  function setSessionTx(tx: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem("paymentTxHash", tx);
  }

  /* -------------------------------------------------
     Wallet refresh (truth = backend)
  ------------------------------------------------- */
  async function refreshWalletState() {
    const tx = getSessionTx();
    if (!tx) {
      setWalletState({ status: "none" });
      return;
    }

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/payment/${tx}`
      );
      if (!res.ok) throw new Error("invalid");

      const p = await res.json();

      if (p.remaining > 0) {
        setWalletState({
          status: "active",
          remaining: p.remaining,
          total: p.total_paid,
        });
      } else {
        setWalletState({ status: "empty" });
      }
    } catch {
      setWalletState({ status: "invalid" });
    }
  }

  /* -------------------------------------------------
     Wallet bootstrap on load
  ------------------------------------------------- */
  useEffect(() => {
    refreshWalletState();
  }, []);

  /* -------------------------------------------------
     Main prompt handler
  ------------------------------------------------- */
  async function askAgent() {
    const p = prompt.trim();
    if (!p) return;

    setLoading(true);
    setError(null);
    setAnswer(null);
    setPaymentDetail(null);

    try {
      const sessionTx = getSessionTx() || undefined;
      const { status, data } = await postPrompt(p, sessionTx);

      if (status === 200) {
        const maybeTx = data?.receipt?.tx_hash;
        if (maybeTx) setSessionTx(maybeTx);

        logPromptEvent(maybeTx);
        setAnswer((data?.answer ?? "").toString());

        await refreshWalletState();
        return;
      }

      if (status === 402) {
        const detail = (data?.detail ?? {}) as PaymentRequiredDetail;
        setPaymentDetail(detail);

        if (
          typeof detail.confirmations === "number" &&
          typeof detail.min_confirmations === "number"
        ) {
          setWalletState({
            status: "pending",
            confirmations: detail.confirmations,
            min: detail.min_confirmations,
          });
        } else {
          setWalletState({ status: "invalid" });
        }

        const existing = getSessionTx();
        if (existing) setTxHash(existing);
        return;
      }

      setError(`Unexpected response (${status})`);
    } catch (e: any) {
      setError(e?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  /* -------------------------------------------------
     Payment confirmation polling
  ------------------------------------------------- */
  async function verifyAndContinue() {
    const tx = txHash.trim();
    if (!tx) return;

    setSessionTx(tx);
    setLoading(true);
    setError(null);

    try {
      for (let i = 0; i < 10; i++) {
        const { status, data } = await postPrompt(prompt.trim(), tx);

        if (status === 200) {
          const maybeTx = data?.receipt?.tx_hash;
          if (maybeTx) setSessionTx(maybeTx);

          logPromptEvent(maybeTx);
          setPaymentDetail(null);
          setAnswer((data?.answer ?? "").toString());

          await refreshWalletState();
          return;
        }

        const detail = (data?.detail ?? {}) as PaymentRequiredDetail;

        if (
          typeof detail.confirmations === "number" &&
          typeof detail.min_confirmations === "number"
        ) {
          setWalletState({
            status: "pending",
            confirmations: detail.confirmations,
            min: detail.min_confirmations,
          });
        }

        setPaymentDetail(detail);
        await sleep(3000);
      }

      setError("Confirmation taking too long. Try again shortly.");
    } catch (e: any) {
      setError(e?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  /* -------------------------------------------------
     Wallet Banner UI
  ------------------------------------------------- */
  const walletBanner = (
    <div className="rounded-xl border border-border bg-card p-4">
      {walletState.status === "none" && (
        <div className="text-sm text-warn">🟡 No active payment</div>
      )}

      {walletState.status === "pending" && (
        <div className="text-sm text-warn">
          ⏳ Payment detected — confirmations{" "}
          {walletState.confirmations}/{walletState.min}
        </div>
      )}

      {walletState.status === "active" && (
        <div className="text-sm text-success">
          🟢 Wallet active — {walletState.remaining} /{" "}
          {walletState.total} USDC
        </div>
      )}

      {walletState.status === "empty" && (
        <div className="text-sm text-danger">🔴 Credit exhausted</div>
      )}

      {walletState.status === "invalid" && (
        <div className="text-sm text-danger">
          ❌ Invalid transaction
        </div>
      )}

      {walletState.status !== "none" && (
        <button
          onClick={() => {
            localStorage.removeItem("paymentTxHash");
            setWalletState({ status: "none" });
            setTxHash("");
          }}
          className="mt-2 text-xs underline text-muted"
        >
          Use a different transaction
        </button>
      )}
    </div>
  );

  /* -------------------------------------------------
     Render
  ------------------------------------------------- */
  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-semibold tracking-tight">
          PromptPay AI
        </h1>
        <p className="text-muted text-lg">
          Usage-metered AI. Pay only when you prompt.
        </p>
      </div>

      {walletBanner}

      <div className="rounded-xl border border-border bg-card p-6 space-y-5">
        <textarea
          rows={6}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask anything…"
          className="w-full rounded-xl border p-4"
        />

        <button
          onClick={askAgent}
          disabled={loading || !prompt.trim()}
          className="rounded-xl bg-accent px-5 py-2.5 text-sm font-medium text-bg"
        >
          {loading ? "Running…" : "Ask Agent"}
        </button>

        {answer && (
          <pre className="whitespace-pre-wrap">{answer}</pre>
        )}
      </div>

      {paymentDetail && (
        <div className="text-sm text-muted">
          Waiting for payment confirmation…
        </div>
      )}
    </div>
  );
}
