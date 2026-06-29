"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ResolveResponse } from "@/lib/types";

const MAX = 4;

// Drives the ?areas=CODE,CODE URL. Server does the fetching/rendering; this just
// edits the set and navigates, so every comparison is shareable and SSR'd.
export function CompareControls({
  current,
}: {
  current: { area_id: string; area_name: string }[];
}) {
  const router = useRouter();
  const [postcode, setPostcode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function navigate(codes: string[]) {
    router.push(codes.length ? `/compare?areas=${codes.join(",")}` : "/compare");
  }

  function remove(code: string) {
    navigate(current.filter((c) => c.area_id !== code).map((c) => c.area_id));
  }

  async function add(e: React.FormEvent) {
    e.preventDefault();
    if (current.length >= MAX) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/resolve?postcode=${encodeURIComponent(postcode.trim())}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail ?? "Postcode not found.");
      const code = (body as ResolveResponse).area.area_id;
      if (current.some((c) => c.area_id === code)) {
        setError("That area is already in the comparison.");
      } else {
        setPostcode("");
        navigate([...current.map((c) => c.area_id), code]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Postcode not found.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      {current.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {current.map((c) => (
            <span
              key={c.area_id}
              className="inline-flex items-center gap-2 rounded-full border border-rule bg-card px-3 py-1 text-sm"
            >
              {c.area_name}
              <button
                type="button"
                onClick={() => remove(c.area_id)}
                aria-label={`Remove ${c.area_name}`}
                className="text-muted hover:text-ink"
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}

      {current.length < MAX ? (
        <form onSubmit={add} className="flex max-w-md gap-2">
          <input
            value={postcode}
            onChange={(e) => setPostcode(e.target.value)}
            placeholder="Add an area by postcode"
            aria-label="Add an area by postcode"
            className="flex-1 rounded-md border border-rule bg-card px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {loading ? "…" : "Add"}
          </button>
        </form>
      ) : (
        <p className="text-xs text-ink2">Comparing the maximum of {MAX} areas.</p>
      )}
      {error && <p className="text-sm text-caution">{error}</p>}
    </div>
  );
}
