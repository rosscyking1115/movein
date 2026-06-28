"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ResolveResponse } from "@/lib/types";
import { areaSlug } from "@/lib/slug";

// Postcode → straight to that neighbourhood's receipt.
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
    <form onSubmit={submit} className="w-full max-w-md">
      <div className="flex gap-2">
        <input
          value={postcode}
          onChange={(e) => setPostcode(e.target.value)}
          placeholder="Enter a UK postcode"
          aria-label="UK postcode"
          className="flex-1 rounded-md border border-rule bg-paper-raised px-4 py-3 text-sm"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-accent px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {loading ? "…" : "Look up"}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-flag">{error}</p>}
    </form>
  );
}
