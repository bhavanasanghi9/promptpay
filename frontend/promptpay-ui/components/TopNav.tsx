"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

function NavLink({
  href,
  label,
}: {
  href: string;
  label: string;
}) {
  const pathname = usePathname();
  const active = pathname === href;

  return (
    <Link
      href={href}
      className={`text-sm transition ${
        active
          ? "text-accent font-medium"
          : "text-muted hover:text-fg"
      }`}
    >
      {label}
    </Link>
  );
}

export default function TopNav() {
  const [hasSession, setHasSession] = useState<boolean | null>(null);

  // Read localStorage AFTER hydration
  useEffect(() => {
    const tx = localStorage.getItem("paymentTxHash");
    setHasSession(!!tx);
  }, []);

  return (
    <div className="sticky top-0 z-50 border-b border-border bg-bg/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        {/* Left */}
        <div className="flex items-center gap-8">
          <div className="text-sm font-semibold tracking-tight">
            PromptPay AI
          </div>

          <nav className="flex items-center gap-6">
            <NavLink href="/" label="Prompt" />
            <NavLink href="/wallet" label="Wallet" />
            <NavLink href="/analytics" label="Analytics" />
          </nav>
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          {hasSession === null ? (
            // Neutral placeholder during hydration
            <div className="rounded-full bg-border/40 px-3 py-1 text-xs text-muted">
              Checking…
            </div>
          ) : (
            <div
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                hasSession
                  ? "bg-success/10 text-success"
                  : "bg-warn/10 text-warn"
              }`}
            >
              {hasSession ? "Wallet Active" : "No Payment"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
