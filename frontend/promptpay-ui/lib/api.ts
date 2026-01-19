export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE) {
  // Helpful warning; app will still run
  // eslint-disable-next-line no-console
  console.warn("NEXT_PUBLIC_API_BASE_URL is not set. Add it in .env.local");
}

export type PaymentRequiredDetail = {
  error?: string;
  agent?: string;
  message?: string;
  payment?: {
    amount: string;
    currency: string;
    chain: string;
    chain_id: number;
    recipient: string;
    retry_header: string;
  };
  // Some of your 402 responses (confirmations/underpayment) don’t include payment{}
  confirmations?: number;
  min_confirmations?: number;
  paid?: string;
  required?: string;
  shortfall?: string;
  tx_hash?: string;
  remaining_credit?: string;
};

export async function postPrompt(prompt: string, txHash?: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (txHash) headers["X-Payment"] = txHash;

  const res = await fetch(`${API_BASE}/prompt`, {
    method: "POST",
    headers,
    body: JSON.stringify({ prompt }),
  });

  const data = await res.json().catch(() => ({}));
  return { status: res.status, data };
}

export function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
