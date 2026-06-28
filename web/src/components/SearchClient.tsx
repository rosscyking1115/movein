"use client";

import { useCallback, useMemo, useState } from "react";
import type { Area, ComponentKey, SearchResponse } from "@/lib/types";
import { COMPONENT_KEYS, COMPONENT_LABELS } from "@/lib/types";
import { reweight } from "@/lib/reweight";
import { AreaCard } from "./AreaCard";

const REGIONS = [
  "North East", "North West", "Yorkshire and The Humber",
  "East Midlands", "West Midlands", "East of England",
  "London", "South East", "South West", "Wales",
];

const WEIGHT_LABELS = ["Ignore", "Low", "Normal", "High"];
const DISPLAY_LIMIT = 50;

type Weights = Record<ComponentKey, number>;
const DEFAULT_WEIGHTS: Weights = {
  affordability_score: 2, safety_score: 2, energy_score: 1,
  flood_score: 1, convenience_score: 2,
};

export function SearchClient({
  initialAreas,
  initialRegions,
}: {
  initialAreas: Area[];
  initialRegions: string[];
}) {
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);
  const [regions, setRegions] = useState<string[]>(initialRegions);
  const [maxRent, setMaxRent] = useState<string>("");
  const [pool, setPool] = useState<Area[]>(initialAreas);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sliders re-rank the visible pool instantly — no network.
  const ranked = useMemo(() => reweight(pool, weights).slice(0, DISPLAY_LIMIT), [pool, weights]);

  // Filters (region / budget) need a fresh pool from the API.
  const applyFilters = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          weights,
          regions: regions.length ? regions : null,
          max_rent: maxRent ? Number(maxRent) : null,
          limit: 200,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Search failed.");
      }
      const data: SearchResponse = await res.json();
      setPool(data.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }, [weights, regions, maxRent]);

  const toggleRegion = (r: string) =>
    setRegions((prev) => (prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]));

  return (
    <div className="grid gap-8 lg:grid-cols-[18rem_1fr]">
      <aside className="space-y-6">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Your priorities
          </h2>
          <p className="mt-1 text-xs text-ink-muted">
            Slide to re-rank instantly. The score is a weighted average of these.
          </p>
          <div className="mt-3 space-y-3">
            {COMPONENT_KEYS.map((k) => (
              <label key={k} className="block">
                <div className="flex items-center justify-between text-sm">
                  <span>{COMPONENT_LABELS[k]}</span>
                  <span className="tnum text-xs text-ink-muted">
                    {WEIGHT_LABELS[weights[k]]}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={3}
                  step={1}
                  value={weights[k]}
                  onChange={(e) =>
                    setWeights((w) => ({ ...w, [k]: Number(e.target.value) }))
                  }
                  className="mt-1 w-full accent-[var(--color-accent)]"
                />
              </label>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Max rent (monthly)
          </h2>
          <input
            type="number"
            inputMode="numeric"
            placeholder="e.g. 1500"
            value={maxRent}
            onChange={(e) => setMaxRent(e.target.value)}
            className="mt-2 w-full rounded-md border border-rule bg-paper-raised px-3 py-2 text-sm"
          />
        </div>

        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Regions
          </h2>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {REGIONS.map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => toggleRegion(r)}
                className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
                  regions.includes(r)
                    ? "border-accent bg-accent-soft text-accent"
                    : "border-rule text-ink-muted hover:border-rule-strong"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={applyFilters}
          disabled={loading}
          className="w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {loading ? "Updating…" : "Apply filters"}
        </button>
        {error && <p className="text-xs text-flag">{error}</p>}
      </aside>

      <section>
        <p className="mb-3 text-sm text-ink-muted">
          Showing the top {ranked.length} of {pool.length} areas in the pool,
          ranked by your priorities.
        </p>
        <div className="space-y-2">
          {ranked.map((area, i) => (
            <AreaCard key={area.area_id} area={area} rank={i + 1} />
          ))}
          {ranked.length === 0 && (
            <p className="text-sm text-ink-muted">
              No areas match those filters. Try widening the budget or regions.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
