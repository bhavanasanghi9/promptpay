"use client";

import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

/* ---------------------------------------------
   Types
--------------------------------------------- */
type PromptEvent = {
  ts: number; // milliseconds
  tx_hash: string | null;
};

type Bucket = {
  date: string;
  count: number;
};

/* ---------------------------------------------
   Helpers
--------------------------------------------- */
function loadEvents(): PromptEvent[] {
  try {
    return JSON.parse(localStorage.getItem("prompt_events") || "[]");
  } catch {
    return [];
  }
}

/**
 * Bucket events by DAY (calendar-correct)
 */
function bucketEventsByDay(events: PromptEvent[]): Bucket[] {
  const buckets: Record<string, number> = {};

  for (const e of events) {
    const d = new Date(e.ts);
    const key = d.toISOString().slice(0, 10); // YYYY-MM-DD
    buckets[key] = (buckets[key] || 0) + 1;
  }

  return Object.entries(buckets)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({
      date: new Date(date).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      }),
      count,
    }));
}

/* ---------------------------------------------
   Page
--------------------------------------------- */
export default function AnalyticsPage() {
  const [events, setEvents] = useState<PromptEvent[]>([]);

  useEffect(() => {
    setEvents(loadEvents());
  }, []);

  const buckets = useMemo(() => bucketEventsByDay(events), [events]);

  /* ---------------------------------------------
     Metrics
  --------------------------------------------- */
  const totalPrompts = events.length;
  const activeDays = buckets.length;
  const avgPerDay =
    activeDays > 0
      ? (totalPrompts / activeDays).toFixed(2)
      : "0.00";

  /* ---------------------------------------------
     Render
  --------------------------------------------- */
  return (
    <div className="mx-auto max-w-6xl space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold">Analytics</h1>
        <p className="text-muted mt-1">
          Usage trends aggregated per day
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Metric title="Total Prompts" value={totalPrompts} />
        <Metric title="Active Days" value={activeDays} />
        <Metric title="Avg Prompts / Day" value={avgPerDay} />
      </div>

      {/* Chart */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <h2 className="text-lg font-medium mb-1">
          Requests over Time
        </h2>
        <p className="text-sm text-muted mb-4">
          Prompts aggregated by calendar day
        </p>

        {buckets.length === 0 ? (
          <div className="text-sm text-muted py-20 text-center">
            No usage yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={buckets}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.05)"
              />
              <XAxis
                dataKey="date"
                stroke="#888"
                tick={{ fontSize: 12 }}
              />
              <YAxis
                allowDecimals={false}
                stroke="#888"
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  background: "#0b1220",
                  border: "1px solid #1e293b",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#2dd4bf"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="text-xs text-muted">
        Data derived from locally logged prompt events.
      </div>
    </div>
  );
}

/* ---------------------------------------------
   Metric Card
--------------------------------------------- */
function Metric({
  title,
  value,
}: {
  title: string;
  value: number | string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <div className="text-sm text-muted">{title}</div>
      <div className="mt-2 text-3xl font-semibold">
        {value}
      </div>
    </div>
  );
}
