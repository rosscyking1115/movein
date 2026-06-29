"use client";

import Link from "next/link";
import { useState } from "react";
import type { Bedrooms, Deal, ListingCheckResponse } from "@/lib/types";
import { gbp, pct, rentPerMonth } from "@/lib/format";
import { buildReceiptRows } from "@/lib/indicators";
import { areaSlug } from "@/lib/slug";

const BEDS: { value: Bedrooms; label: string }[] = [
  { value: "any", label: "Any" },
  { value: "1", label: "1" },
  { value: "2", label: "2" },
  { value: "3", label: "3" },
  { value: "4plus", label: "4+" },
];

function toggleClass(active: boolean) {
  return `rounded-[8px] border px-3 py-2 text-sm ${
    active ? "border-accent bg-accent text-white" : "border-rule2 bg-card2 text-ink2 hover:text-ink"
  }`;
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
        body: JSON.stringify({ postcode: postcode.trim(), deal, bedrooms, asking_gbp: Number(asking) }),
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

  const price = result?.price ?? null;
  const ratio = price?.pct_vs_local == null ? 1 : 1 + price.pct_vs_local / 100;
  const markerLeft = Math.max(4, Math.min(96, 50 + (ratio - 1) * 220));
  const caution = price?.band.startsWith("well above") ?? false;
  const bandAccent = caution ? "var(--caution)" : "var(--accent)";
  const money = (v: number | null | undefined) => (deal === "rent" ? rentPerMonth(v) : gbp(v));

  return (
    <div className="grid items-start gap-[26px] lg:grid-cols-[minmax(0,340px)_minmax(0,1fr)]">
      {/* Form */}
      <form onSubmit={submit} className="rounded-[16px] border border-rule2 bg-card p-[22px]">
        <div className="mb-[18px] font-mono text-[11px] uppercase tracking-[.12em] text-ink">The listing</div>

        <label htmlFor="ck-postcode" className="mb-1.5 block text-[13px] text-ink2">Postcode</label>
        <input
          id="ck-postcode"
          required
          value={postcode}
          onChange={(e) => setPostcode(e.target.value)}
          placeholder="e.g. SW4 7AA"
          className="mb-[18px] min-h-[44px] w-full rounded-[9px] border border-rule2 bg-card2 px-3 py-[11px] text-sm text-ink"
        />

        <div className="mb-1.5 text-[13px] text-ink2">Deal</div>
        <div role="group" className="mb-[18px] flex gap-1.5">
          {(["rent", "buy"] as Deal[]).map((d) => (
            <button key={d} type="button" onClick={() => setDeal(d)} aria-pressed={deal === d} className={`flex-1 ${toggleClass(deal === d)}`}>
              {d === "rent" ? "To rent" : "To buy"}
            </button>
          ))}
        </div>

        <div className="mb-1.5 text-[13px] text-ink2">Bedrooms</div>
        <div role="group" className="mb-[18px] flex flex-wrap gap-1.5">
          {BEDS.map((b) => (
            <button key={b.value} type="button" onClick={() => setBedrooms(b.value)} aria-pressed={bedrooms === b.value} className={toggleClass(bedrooms === b.value)}>
              {b.label}
            </button>
          ))}
        </div>

        <label htmlFor="ck-ask" className="mb-1.5 block text-[13px] text-ink2">
          {deal === "rent" ? "Asking rent (monthly)" : "Asking price"}
        </label>
        <div className="flex items-center gap-2 rounded-[9px] border border-rule2 bg-card2 px-3.5">
          <span className="font-mono text-base text-muted">£</span>
          <input
            id="ck-ask"
            required
            inputMode="numeric"
            value={asking}
            onChange={(e) => setAsking(e.target.value)}
            placeholder={deal === "rent" ? "1400" : "350000"}
            className="min-w-0 flex-1 border-none bg-transparent py-3 font-mono text-base text-ink outline-none"
          />
        </div>

        <button type="submit" disabled={loading} className="mt-[18px] w-full rounded-[10px] bg-accent px-5 py-3 text-sm font-semibold text-white disabled:opacity-60">
          {loading ? "Checking…" : "Check this listing"}
        </button>
        {error && <p className="mt-2 text-sm text-caution">{error}</p>}
      </form>

      {/* Result */}
      <div className="flex flex-col gap-[18px]">
        {result && price ? (
          <>
            <div className="rounded-[16px] border bg-card p-6" style={{ borderColor: caution ? "var(--caution)" : "var(--rule2)" }}>
              <div className="mb-[18px] flex flex-wrap items-baseline justify-between gap-2.5">
                <div>
                  <div className="mb-[7px] font-mono text-[11px] uppercase capitalize tracking-[.12em]" style={{ color: bandAccent }}>
                    {price.band}
                  </div>
                  <div className="max-w-[380px] text-[15px] leading-[1.5] text-ink2">
                    {money(Number(asking))} against {price.basis}. Asking isn&rsquo;t achieved price — a prompt to look closer, not a valuation.
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted">Local typical</div>
                  <div className="font-mono text-xl text-ink">{money(price.local_typical_gbp)}</div>
                </div>
              </div>
              {/* Band scale */}
              <div className="relative my-2 h-[46px]">
                <div className="absolute inset-x-0 top-[18px] h-2 rounded-[5px] border border-rule" style={{ background: "linear-gradient(90deg,var(--card2),var(--bar-track))" }} />
                <div className="absolute top-[14px] left-1/2 h-4 w-0.5 -translate-x-1/2 bg-rule2" />
                <div className="absolute top-[34px] left-1/2 -translate-x-1/2 font-mono text-[10px] text-muted">typical</div>
                <div className="absolute top-2 -translate-x-1/2 transition-[left] duration-500 ease-[cubic-bezier(.22,.61,.36,1)]" style={{ left: `${markerLeft}%` }}>
                  <div className="mx-auto h-7 w-[3px] rounded-[2px]" style={{ background: bandAccent }} />
                </div>
                <div className="absolute top-[-2px] -translate-x-1/2 whitespace-nowrap font-mono text-xs font-semibold transition-[left] duration-500 ease-[cubic-bezier(.22,.61,.36,1)]" style={{ left: `${markerLeft}%`, color: bandAccent }}>
                  {pct(price.pct_vs_local)}
                </div>
              </div>
              <div className="mt-0.5 flex justify-between font-mono text-[10.5px] text-muted">
                <span>well below</span><span>below</span><span>around</span><span>above</span><span>well above</span>
              </div>
            </div>

            {/* Mini receipt */}
            <div className="rounded-[16px] border border-rule2 bg-card p-[22px]">
              <div className="mb-1.5 flex items-baseline justify-between">
                <div className="font-display text-2xl font-bold text-ink">{result.area.area_name}</div>
                <Link href={`/area/${areaSlug(result.area.area_id, result.area.area_name)}`} className="text-[13px] font-semibold text-accent hover:underline">
                  Full receipt →
                </Link>
              </div>
              <div className="mb-4 text-[13px] text-muted">
                {[result.area.local_authority_name, result.area.region].filter(Boolean).join(" · ")}
              </div>
              {buildReceiptRows(result.area).map((r) => (
                <div key={r.key} className="flex items-center justify-between gap-3 border-t border-rule py-2.5">
                  <div className="min-w-[110px] text-[13.5px] text-ink">{r.name}</div>
                  <div className="h-[5px] max-w-[120px] flex-1 overflow-hidden rounded-[3px] bg-bar-track">
                    <div className="h-full rounded-[3px] bg-bar" style={{ width: r.hasData ? r.barWidth : 0 }} />
                  </div>
                  <div className="min-w-[46px] text-right font-mono text-[13px] text-ink2">{r.hasData ? r.scoreText : "—"}</div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="rounded-[16px] border border-dashed border-rule2 bg-card px-6 py-16 text-center text-sm text-muted">
            Enter a postcode and an asking price to see how it sits against the
            local typical — with the area schedule beneath it.
          </div>
        )}
      </div>
    </div>
  );
}
