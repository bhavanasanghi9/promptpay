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
      const res = await fetch(`http://localhost:8000/payment/${tx}`);
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
     Payment Required UI
  ------------------------------------------------- */
  const paymentUI = paymentDetail ? (
    <div className="rounded-xl border border-warn/40 bg-warn/10 p-5 space-y-4">
      <div>
        <div className="text-sm font-medium text-warn">
          Payment Required
        </div>
        <div className="mt-1 text-sm text-muted">
          {paymentDetail.message ??
            paymentDetail.error ??
            "Provide a valid transaction hash to continue."}
        </div>
      </div>

      {paymentDetail.payment ? (
        <div className="rounded-xl border border-border bg-bg/40 p-4 space-y-2">
          <div className="text-sm text-muted">Send</div>
          <div className="text-lg font-semibold">
            {paymentDetail.payment.amount}{" "}
            {paymentDetail.payment.currency}
          </div>
          <div className="text-sm text-muted">To (agent wallet)</div>
          <code className="block break-all text-xs">
            {paymentDetail.payment.recipient}
          </code>
        </div>
      ) : null}

      {typeof paymentDetail.confirmations === "number" &&
      typeof paymentDetail.min_confirmations === "number" ? (
        <div className="text-xs text-muted">
          Confirmations:{" "}
          <span className="text-fg font-medium">
            {paymentDetail.confirmations}/
            {paymentDetail.min_confirmations}
          </span>
        </div>
      ) : null}

      <div className="space-y-2">
        <div className="text-sm text-muted">Transaction hash</div>
        <input
          value={txHash}
          onChange={(e) => setTxHash(e.target.value)}
          placeholder="0x…"
          className="
            w-full rounded-xl border border-border bg-bg/50 px-4 py-2 text-sm
            text-fg placeholder:text-muted shadow-soft
            focus:outline-none focus:ring-2 focus:ring-accent/40
          "
        />

        <button
          onClick={verifyAndContinue}
          disabled={loading || !txHash.trim()}
          className="
            inline-flex items-center justify-center rounded-xl
            bg-accent px-5 py-2.5 text-sm font-medium text-bg transition
            hover:bg-accent/90 disabled:opacity-60
          "
        >
          {loading ? "Confirming…" : "Verify & Continue"}
        </button>

        <div className="text-xs text-muted">
          We’ll retry automatically until confirmations are sufficient.
        </div>
      </div>
    </div>
  ) : null;

  /* -------------------------------------------------
     Wallet Banner UI
  ------------------------------------------------- */
  const walletBanner = (
    <div className="rounded-xl border border-border bg-card p-4">
      {walletState.status === "none" && (
        <div className="text-sm text-warn">
          🟡 No active payment
        </div>
      )}

      {walletState.status === "active" && (
        <div className="text-sm text-success">
          🟢 Wallet active — {walletState.remaining} /{" "}
          {walletState.total} USDC
        </div>
      )}

      {walletState.status === "empty" && (
        <div className="text-sm text-danger">
          🔴 Credit exhausted
        </div>
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
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-semibold tracking-tight">
          PromptPay AI
        </h1>
        <p className="text-muted text-lg">
          Usage-metered AI. Pay only when you prompt.
        </p>
      </div>

      {walletBanner}

      {/* Prompt Card */}
      <div className="rounded-xl border border-border bg-card p-6 space-y-5">
        <div>
          <h2 className="text-lg font-medium">Ask the Agent</h2>
          <p className="text-sm text-muted">
            Each prompt consumes a fixed amount of USDC.
          </p>
        </div>

        <textarea
          rows={6}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask anything…"
          className="
            w-full resize-none rounded-xl border border-border bg-bg/50
            p-4 text-sm text-fg placeholder:text-muted shadow-soft
            focus:outline-none focus:ring-2 focus:ring-accent/40
          "
        />

        <div className="flex items-center justify-between">
          <button
            onClick={askAgent}
            disabled={loading || !prompt.trim()}
            className="
              rounded-xl bg-accent px-5 py-2.5 text-sm font-medium text-bg
              hover:bg-accent/90 disabled:opacity-60
            "
          >
            {loading ? "Running…" : "Ask Agent"}
          </button>

          <div className="text-sm text-muted">
            Price:{" "}
            <span className="text-fg font-medium">
              {priceLabel}
            </span>{" "}
            per prompt
          </div>
        </div>

        {error ? (
          <div className="rounded-xl border border-danger/40 bg-danger/10 p-4 text-sm">
            <div className="font-medium text-danger">Error</div>
            <div className="mt-1 text-muted">{error}</div>
          </div>
        ) : null}

        {answer ? (
          <div className="rounded-xl border border-success/40 bg-success/10 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-success">
              <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-success text-bg">
                ✓
              </span>
              Prompt executed successfully
            </div>
            <pre className="mt-3 whitespace-pre-wrap text-[15px] leading-6">
              {answer}
            </pre>
          </div>
        ) : null}
      </div>

      {/* Payment UI */}
      {paymentUI}

      {/* Footer */}
      <div className="text-xs text-muted">
        Usage events are logged locally to power time-based analytics.
      </div>
    </div>
  );
}
