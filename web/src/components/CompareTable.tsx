import Link from "next/link";
import type { Area, ComponentKey } from "@/lib/types";
import { COMPONENT_LABELS } from "@/lib/types";
import { areaSlug } from "@/lib/slug";
import { gbp, km, rate, ratingOrDash, rentPerMonth, score } from "@/lib/format";

type Row = {
  label: string;
  value: (a: Area) => string;
  // Score rows: higher ranks better, so we bold the leader. Fact rows stay
  // neutral — "lower rent" isn't universally "better", and we don't do verdicts.
  rank?: (a: Area) => number | null;
};

const SCORE_ROWS: Row[] = [
  { label: "Overall", value: (a) => score(a.overall_score), rank: (a) => a.overall_score },
  ...(
    [
      "affordability_score",
      "safety_score",
      "energy_score",
      "flood_score",
      "convenience_score",
    ] as ComponentKey[]
  ).map((k) => ({
    label: COMPONENT_LABELS[k],
    value: (a: Area) => score(a[k]),
    rank: (a: Area) => a[k],
  })),
];

const FACT_ROWS: Row[] = [
  { label: "Typical rent", value: (a) => rentPerMonth(a.official_rent_monthly_gbp) },
  { label: "1-bed rent", value: (a) => rentPerMonth(a.rent_1bed_gbp) },
  { label: "2-bed rent", value: (a) => rentPerMonth(a.rent_2bed_gbp) },
  { label: "3-bed rent", value: (a) => rentPerMonth(a.rent_3bed_gbp) },
  { label: "4+ bed rent", value: (a) => rentPerMonth(a.rent_4plus_gbp) },
  { label: "Median sale price", value: (a) => gbp(a.median_sale_price_gbp) },
  { label: "Median EPC", value: (a) => ratingOrDash(a.epc_median_rating) },
  { label: "Crime / 1,000", value: (a) => rate(a.crime_rate_per_1000) },
  { label: "Flood risk", value: (a) => a.flood_risk_flag ?? "—" },
  { label: "Walkable amenities", value: (a) => (a.walkable_amenity_count ?? "—").toString() },
  { label: "Nearest station", value: (a) => km(a.nearest_station_km) },
  { label: "Nearest supermarket", value: (a) => km(a.nearest_supermarket_km) },
  { label: "Nearest GP", value: (a) => km(a.nearest_gp_km) },
  { label: "Nearest school", value: (a) => km(a.nearest_school_km) },
  { label: "Nearest greenspace", value: (a) => km(a.nearest_greenspace_km) },
];

function leaderIndex(areas: Area[], rank?: (a: Area) => number | null): number {
  if (!rank) return -1;
  let best = -Infinity;
  let idx = -1;
  areas.forEach((a, i) => {
    const v = rank(a);
    if (v != null && v > best) {
      best = v;
      idx = i;
    }
  });
  return idx;
}

function Section({ title, rows, areas }: { title: string; rows: Row[]; areas: Area[] }) {
  return (
    <>
      <tr>
        <th
          colSpan={areas.length + 1}
          className="bg-paper px-3 pb-1 pt-5 text-left text-xs font-semibold uppercase tracking-wide text-ink-faint"
        >
          {title}
        </th>
      </tr>
      {rows.map((row) => {
        const leader = leaderIndex(areas, row.rank);
        return (
          <tr key={row.label} className="rule-b">
            <th scope="row" className="px-3 py-2 text-left text-sm font-normal text-ink-muted">
              {row.label}
            </th>
            {areas.map((a, i) => (
              <td
                key={a.area_id}
                className={`tnum px-3 py-2 text-right text-sm ${
                  i === leader ? "font-semibold text-ink" : ""
                }`}
              >
                {row.value(a)}
              </td>
            ))}
          </tr>
        );
      })}
    </>
  );
}

export function CompareTable({ areas }: { areas: Area[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[36rem] border-collapse">
        <thead>
          <tr className="rule-b">
            <th className="px-3 py-2 text-left" />
            {areas.map((a) => (
              <th key={a.area_id} className="px-3 py-2 text-right align-bottom">
                <Link
                  href={`/area/${areaSlug(a.area_id, a.area_name)}`}
                  className="font-semibold hover:text-accent"
                >
                  {a.area_name}
                </Link>
                <div className="text-xs font-normal text-ink-muted">
                  {a.local_authority_name ?? a.region}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <Section title="Scores" rows={SCORE_ROWS} areas={areas} />
          <Section title="The facts behind them" rows={FACT_ROWS} areas={areas} />
        </tbody>
      </table>
    </div>
  );
}
