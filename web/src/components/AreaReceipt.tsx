import { ScoreBar } from "./ScoreBar";
import type { Area, ComponentKey } from "@/lib/types";
import { COMPONENT_LABELS } from "@/lib/types";
import { gbp, km, rate, ratingOrDash, rentPerMonth, score } from "@/lib/format";

// The trade-off receipt: every component score sits beside the raw fact behind
// it, so a number is never asked to be trusted on its own.

const COMPONENT_FACT: Record<ComponentKey, (a: Area) => string> = {
  affordability_score: (a) => `Typical rent ${rentPerMonth(a.official_rent_monthly_gbp)}`,
  safety_score: (a) =>
    a.crime_rate_per_1000 == null
      ? "Crime rate unavailable"
      : `${rate(a.crime_rate_per_1000)} crimes per 1,000 residents`,
  energy_score: (a) => `Median EPC rating ${ratingOrDash(a.epc_median_rating)}`,
  flood_score: (a) => `Flood risk: ${a.flood_risk_flag ?? "unknown"}`,
  convenience_score: (a) =>
    a.walkable_amenity_count == null
      ? "Walkable amenities unavailable"
      : `${a.walkable_amenity_count} amenities within walking distance`,
};

const COMPONENT_ORDER: ComponentKey[] = [
  "affordability_score",
  "safety_score",
  "energy_score",
  "flood_score",
  "convenience_score",
];

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rule-b flex items-baseline justify-between gap-4 py-2">
      <dt className="text-sm text-ink-muted">{label}</dt>
      <dd className="tnum text-sm">{value}</dd>
    </div>
  );
}

export function AreaReceipt({ area }: { area: Area }) {
  return (
    <div className="space-y-8">
      {/* Header: the headline number, stated as an indicator. */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{area.area_name}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            {[area.local_authority_name, area.region].filter(Boolean).join(" · ")}
          </p>
        </div>
        <div className="text-right">
          <div className="tnum text-4xl font-semibold leading-none">
            {score(area.overall_score)}
            <span className="text-lg text-ink-faint">/100</span>
          </div>
          <p className="mt-1 text-xs uppercase tracking-wide text-ink-faint">
            overall indicator
            {area.confidence_level ? ` · ${area.confidence_level} confidence` : ""}
          </p>
        </div>
      </div>

      {area.why_this_area && (
        <p className="border-l-2 border-accent bg-accent-soft/50 px-4 py-3 text-sm">
          {area.why_this_area}
        </p>
      )}

      {/* The component ledger — score beside its fact. */}
      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-faint">
          What goes into the score
        </h2>
        <div className="space-y-3">
          {COMPONENT_ORDER.map((key) => (
            <div key={key} className="grid grid-cols-1 gap-1 sm:grid-cols-[10rem_1fr] sm:items-center sm:gap-4">
              <div className="text-sm font-medium">{COMPONENT_LABELS[key]}</div>
              <div className="space-y-1">
                <ScoreBar value={area[key]} />
                <p className="text-xs text-ink-muted">{COMPONENT_FACT[key](area)}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* The raw facts, in full. */}
      <section className="grid gap-x-10 gap-y-0 sm:grid-cols-2">
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">
            Cost
          </h2>
          <dl>
            <Fact label="Typical rent (all)" value={rentPerMonth(area.official_rent_monthly_gbp)} />
            <Fact label="1-bed rent" value={rentPerMonth(area.rent_1bed_gbp)} />
            <Fact label="2-bed rent" value={rentPerMonth(area.rent_2bed_gbp)} />
            <Fact label="3-bed rent" value={rentPerMonth(area.rent_3bed_gbp)} />
            <Fact label="4+ bed rent" value={rentPerMonth(area.rent_4plus_gbp)} />
            <Fact label="Median sale price" value={gbp(area.median_sale_price_gbp)} />
          </dl>
        </div>
        <div>
          <h2 className="mb-2 mt-6 text-xs font-semibold uppercase tracking-wide text-ink-faint sm:mt-0">
            Place &amp; access
          </h2>
          <dl>
            <Fact label="Median EPC rating" value={ratingOrDash(area.epc_median_rating)} />
            <Fact label="Crime per 1,000" value={rate(area.crime_rate_per_1000)} />
            <Fact label="Flood risk" value={area.flood_risk_flag ?? "—"} />
            <Fact label="Nearest station" value={km(area.nearest_station_km)} />
            <Fact label="Nearest supermarket" value={km(area.nearest_supermarket_km)} />
            <Fact label="Nearest GP" value={km(area.nearest_gp_km)} />
            <Fact label="Nearest school" value={km(area.nearest_school_km)} />
            <Fact label="Nearest greenspace" value={km(area.nearest_greenspace_km)} />
          </dl>
        </div>
      </section>
    </div>
  );
}
