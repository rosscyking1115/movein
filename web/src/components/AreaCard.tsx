import Link from "next/link";
import type { Area, ComponentKey } from "@/lib/types";
import { COMPONENT_LABELS } from "@/lib/types";
import { areaSlug } from "@/lib/slug";
import { rentPerMonth, score } from "@/lib/format";
import { ScoreBar } from "./ScoreBar";

const MINI: ComponentKey[] = [
  "affordability_score",
  "safety_score",
  "energy_score",
  "flood_score",
  "convenience_score",
];

// A compact result row: the match score, the place, and the component mix that
// produced it — so the ranking is legible at a glance, not a black box.
export function AreaCard({ area, rank }: { area: Area; rank?: number }) {
  const shown = area.match_score ?? area.overall_score;
  return (
    <Link
      href={`/area/${areaSlug(area.area_id, area.area_name)}`}
      className="block rounded-card border border-rule bg-paper-raised px-4 py-3 transition-colors hover:border-rule-strong"
    >
      <div className="flex items-center gap-4">
        {rank != null && (
          <span className="tnum w-6 shrink-0 text-sm text-ink-faint">{rank}</span>
        )}
        <div className="min-w-0 flex-1">
          <div className="truncate font-medium">{area.area_name}</div>
          <div className="truncate text-xs text-ink-muted">
            {[area.local_authority_name, area.region].filter(Boolean).join(" · ")}
            {area.official_rent_monthly_gbp != null &&
              ` · ${rentPerMonth(area.official_rent_monthly_gbp)}`}
          </div>
        </div>
        <div className="tnum shrink-0 text-2xl font-semibold leading-none">
          {score(shown)}
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-5">
        {MINI.map((k) => (
          <div key={k} className="min-w-0">
            <div className="truncate text-[10px] uppercase tracking-wide text-ink-faint">
              {COMPONENT_LABELS[k]}
            </div>
            <ScoreBar value={area[k]} width="compact" />
          </div>
        ))}
      </div>
    </Link>
  );
}
