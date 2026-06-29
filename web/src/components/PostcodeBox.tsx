"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ResolveResponse } from "@/lib/types";
import { areaSlug } from "@/lib/slug";

// Postcode → straight to that neighbourhood's schedule.
export function PostcodeBox() {
  const router = useRouter();
  const [postcode, setPostcode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/resolve?postcode=${encodeURIComponent(postcode.trim())}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? "Postcode not found.");
      const data = body as ResolveResponse;
      router.push(`/area/${areaSlug(data.area.area_id, data.area.area_name)}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Postcode not found.");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={submit} className="max-w-[520px]">
      <div className="flex items-center gap-2.5 rounded-[10px] border border-rule2 bg-card py-1.5 pl-4 pr-1.5">
        <span className="font-mono text-[13px] text-muted">Postcode</span>
        <input
          value={postcode}
          onChange={(e) => setPostcode(e.target.value)}
          placeholder="e.g. M21 9HZ"
          aria-label="Enter a postcode"
          className="min-w-0 flex-1 border-none bg-transparent py-2 font-mono text-base tracking-[.04em] text-ink outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="h-[42px] rounded-[7px] bg-accent px-[18px] text-sm font-semibold text-white disabled:opacity-60"
        >
          {loading ? "…" : "Look up"}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-caution">{error}</p>}
    </form>
  );
}
