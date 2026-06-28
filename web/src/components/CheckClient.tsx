"use client";

import { useState } from "react";
import type { Bedrooms, Deal, ListingCheckResponse } from "@/lib/types";
import { gbp, pct, rentPerMonth } from "@/lib/format";
import { AreaReceipt } from "./AreaReceipt";

const BEDROOMS: { value: Bedrooms; label: string }[] = [
  { value: "any", label: "Any" },
  { value: "1", label: "1 bed" },
  { value: "2", label: "2 bed" },
  { value: "3", label: "3 bed" },
  { value: "4plus", label: "4+ bed" },
];

// "Well above" is the only band we visually flag — and even then in amber, as a
// prompt to look closer, not a red "bad deal" verdict.
function bandTone(band: string): string {
  return band.startsWith("well above")
    ? "border-flag bg-flag-soft text-flag"
    : "border-rule bg-accent-soft/60 text-ink";
}

export function CheckClient() {
  const [postcode, setPostcode] = useState("");
  const [deal, setDeal] = useState<Deal>("rent");
  const [bedrooms, setBedrooms] = useState<Bedrooms>("any");
  const [asking, setAsking] = useState("");
  const [result, setResult] = useState<ListingCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/listing-check", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          postcode: postcode.trim(),
          deal,
          bedrooms,
          asking_gbp: Number(asking),
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? "Could not check that listing.");
      setResult(body as ListingCheckResponse);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not check that listing.");
    } finally {
      setLoading(false);
    }
  }

  const askingMoney = deal === "rent" ? rentPerMonth(Number(asking) || null) : gbp(Number(asking) || null);

  return (
    <div className="space-y-8">
      <form
        onSubmit={submit}
        className="grid gap-4 rounded-card border border-rule bg-paper-raised p-5 sm:grid-cols-2"
      >
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Postcode
          </span>
          <input
            required
            value={postcode}
            onChange={(e) => setPostcode(e.target.value)}
            placeholder="e.g. SW4 7AA"
            className="mt-1 w-full rounded-md border border-rule bg-paper px-3 py-2 text-sm"
          />
        </label>

        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            {deal === "rent" ? "Asking rent (monthly)" : "Asking price"}
          </span>
          <input
            required
            type="number"
            inputMode="numeric"
            value={asking}
            onChange={(e) => setAsking(e.target.value)}
            placeholder={deal === "rent" ? "e.g. 1400" : "e.g. 350000"}
            className="mt-1 w-full rounded-md border border-rule bg-paper px-3 py-2 text-sm"
          />
        </label>

        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Deal
          </span>
          <div className="mt-1 flex gap-2">
            {(["rent", "buy"] as Deal[]).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDeal(d)}
                className={`flex-1 rounded-md border px-3 py-2 text-sm capitalize ${
                  deal === d ? "border-accent bg-accent-soft text-accent" : "border-rule text-ink-muted"
                }`}
              >
                {d === "rent" ? "Renting" : "Buying"}
              </button>
            ))}
          </div>
        </div>

        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Bedrooms
          </span>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {BEDROOMS.map((b) => (
              <button
                key={b.value}
                type="button"
                onClick={() => setBedrooms(b.value)}
                className={`rounded-md border px-2.5 py-2 text-xs ${
                  bedrooms === b.value ? "border-accent bg-accent-soft text-accent" : "border-rule text-ink-muted"
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

        <div className="sm:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-white disabled:opacity-60"
          >
            {loading ? "Checking…" : "Check this listing"}
          </button>
          {error && <p className="mt-2 text-sm text-flag">{error}</p>}
        </div>
      </form>

      {result && (
        <div className="space-y-8">
          {result.price && (
            <div className={`rounded-card border px-5 py-4 ${bandTone(result.price.band)}`}>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="text-sm">
                  {askingMoney} is{" "}
                  <strong className="font-semibold">{result.price.band}</strong>
                </span>
                <span className="tnum text-sm">
                  {pct(result.price.pct_vs_local)} vs{" "}
                  {deal === "rent"
                    ? rentPerMonth(result.price.local_typical_gbp)
                    : gbp(result.price.local_typical_gbp)}
                </span>
              </div>
              <p className="mt-1 text-xs opacity-80">
                Compared against {result.price.basis}. An area-level sanity check,
                not a valuation — asking ≠ achieved.
              </p>
            </div>
          )}
          <AreaReceipt area={result.area} />
        </div>
      )}
    </div>
  );
}
