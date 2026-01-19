"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";
import { shortTx, arcTxUrl, arcAddressUrl } from "@/lib/format";



type Payment = {
  tx_hash: string;
  from: string;
  total_paid: number;
  consumed: number;
  remaining: number;
  uses: number;
};

type Revenue = {
  total_revenue_usdc: number;
  total_consumed_usdc: number;
  total_remaining_credits: number;
  total_prompts_served: number;
  price_per_prompt: string;
  agent_wallet: string;
};

export default function WalletPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [revenue, setRevenue] = useState<Revenue | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [pRes, rRes] = await Promise.all([
          fetch(`${API_BASE}/payments`).then((r) => r.json()),
          fetch(`${API_BASE}/revenue`).then((r) => r.json()),
        ]);

        setPayments(pRes.payments || []);
        setRevenue(rRes);
      } catch (e) {
        console.error("Failed to load wallet data", e);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) {
    return <div className="text-muted">Loading wallet…</div>;
  }

  const totalPaid = revenue?.total_revenue_usdc ?? 0;
  const totalRemaining = revenue?.total_remaining_credits ?? 0;
  const pct =
    totalPaid > 0 ? Math.min(100, (totalRemaining / totalPaid) * 100) : 0;

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Wallet</h1>
        <p className="text-muted mt-1">
          View your credit balance, payments, and usage.
        </p>
      </div>

      {/* Agent Wallet Info */}
<div className="rounded-xl border border-border bg-card p-6 space-y-3">
  <div className="text-sm text-muted">Agent Wallet</div>

  <div className="flex items-center gap-3">
    <code className="text-xs break-all font-mono text-fg">
      {revenue?.agent_wallet}
    </code>

    <button
      onClick={() =>
        navigator.clipboard.writeText(revenue?.agent_wallet || "")
      }
      className="
        text-xs text-accent hover:underline
      "
    >
      Copy
    </button>
  </div>

  <div className="flex items-center justify-between pt-2">
    <div>
      <div className="text-xs text-muted">Total Payments Recevied</div>
      <div className="text-lg font-semibold">
        {revenue?.total_revenue_usdc} USDC
      </div>
    </div>

    {revenue?.agent_wallet && (
      <a
        href={arcAddressUrl(revenue.agent_wallet)}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-accent hover:underline"
      >
        View on Explorer →
      </a>
    )}
  </div>
</div>


      {/* Credit summary */}
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-muted">Remaining Credit</div>
            <div className="text-2xl font-semibold">
              {totalRemaining} USDC
            </div>
          </div>
          <div className="text-sm text-muted">
            Price per prompt:{" "}
            <span className="text-fg font-medium">
              {revenue?.price_per_prompt} USDC
            </span>
          </div>
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full bg-accent transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>

        <div className="text-xs text-muted">
          {pct.toFixed(1)}% of paid credit remaining
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
      <StatCard
  label="Total Payments Received"
  value={`${revenue?.total_revenue_usdc} USDC`}
/>

<StatCard
  label="Credit Used"
  value={`${revenue?.total_consumed_usdc} USDC`}
/>

<StatCard
  label="Credit Remaining"
  value={`${revenue?.total_remaining_credits} USDC`}
/>

<StatCard
  label="Prompts Served"
  value={`${revenue?.total_prompts_served}`}
/>

      </div>

      {/* Payments table */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-lg font-medium mb-4">Payments</h2>

        {payments.length === 0 ? (
          <div className="text-sm text-muted">No payments yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted border-b border-border">
                  <th className="py-2 text-left">Transaction</th>
                  <th className="py-2 text-right">Paid</th>
                  <th className="py-2 text-right">Remaining</th>
                  <th className="py-2 text-right">Uses</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr
                    key={p.tx_hash}
                    className="border-b border-border/60"
                  >
                    <td className="py-2 font-mono text-xs break-all">
  <a
    href={`https://testnet.arcscan.app/tx/${p.tx_hash}`}
    target="_blank"
    rel="noopener noreferrer"
    className="text-accent hover:underline"
  >
    {p.tx_hash}
    <span className="ml-1 text-[10px] opacity-70">🔗</span>
  </a>
</td>

                    <td className="py-2 text-right">
                      {p.total_paid}
                    </td>
                    <td className="py-2 text-right">
                      {p.remaining}
                    </td>
                    <td className="py-2 text-right">
                      {p.uses}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
    </div>
  );
}
