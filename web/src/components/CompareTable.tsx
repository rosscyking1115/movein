import Link from "next/link";
import type { Area, ComponentKey } from "@/lib/types";
import { COMPONENT_LABELS } from "@/lib/types";
import { areaSlug } from "@/lib/slug";
import { gbp, km, rate, ratingOrDash, rentPerMonth, score } from "@/lib/format";

type ScoreRow = { label: string; rank: (a: Area) => number | null };
type FactRow = { label: string; value: (a: Area) => string };

const SCORE_ROWS: ScoreRow[] = [
  { label: "Overall", rank: (a) => a.overall_score },
  ...(["affordability_score", "safety_score", "energy_score", "flood_score", "convenience_score"] as ComponentKey[]).map(
    (k) => ({ label: COMPONENT_LABELS[k], rank: (a: Area) => a[k] }),
  ),
];

const FACT_ROWS: FactRow[] = [
  { label: "Typical rent", value: (a) => rentPerMonth(a.official_rent_monthly_gbp) },
  { label: "2-bed rent", value: (a) => rentPerMonth(a.rent_2bed_gbp) },
  { label: "Median sale price", value: (a) => gbp(a.median_sale_price_gbp) },
  { label: "Median EPC", value: (a) => ratingOrDash(a.epc_median_rating) },
  { label: "Crime / 1,000", value: (a) => rate(a.crime_rate_per_1000) },
  { label: "Flood risk", value: (a) => a.flood_risk_flag ?? "—" },
  { label: "Walkable amenities", value: (a) => (a.walkable_amenity_count ?? "—").toString() },
  { label: "Nearest station", value: (a) => km(a.nearest_station_km) },
];

function leaderIndex(areas: Area[], rank: (a: Area) => number | null): number {
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

const stickyTh = "sticky left-0 z-10 bg-card text-left";

export function CompareTable({ areas }: { areas: Area[] }) {
  return (
    <div className="overflow-x-auto rounded-[16px] border border-rule2 bg-card">
      <table className="w-full min-w-[560px] border-collapse">
        <thead>
          <tr>
            <th scope="col" className={`${stickyTh} border-b border-rule2 px-5 py-[18px] text-xs font-semibold uppercase tracking-[.08em] text-muted`}>
              Indicator
            </th>
            {areas.map((a) => (
              <th key={a.area_id} scope="col" className="min-w-[140px] border-b border-rule2 px-[18px] py-[18px] text-left align-bottom">
                <Link
                  href={`/area/${areaSlug(a.area_id, a.area_name)}`}
                  className="block font-display text-[21px] font-bold leading-[1.05] text-ink hover:text-accent"
                >
                  {a.area_name}
                </Link>
                <span className="text-xs text-muted">{a.local_authority_name ?? a.region}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <BandRow span={areas.length + 1} accent>Scores · neutral 0–100</BandRow>
          {SCORE_ROWS.map((row) => {
            const leader = leaderIndex(areas, row.rank);
            return (
              <tr key={row.label}>
                <th scope="row" className={`${stickyTh} border-b border-rule px-5 py-[13px] text-sm font-medium text-ink2`}>
                  {row.label}
                </th>
                {areas.map((a, i) => {
                  const v = row.rank(a);
                  return (
                    <td key={a.area_id} className="border-b border-rule px-[18px] py-[13px]">
                      <div className="flex items-center gap-[9px]">
                        <span className={`min-w-[30px] font-mono text-[15px] ${i === leader ? "font-semibold text-ink" : "text-ink2"}`}>
                          {score(v)}
                        </span>
                        <div className="h-[5px] max-w-[70px] flex-1 overflow-hidden rounded-[3px] bg-bar-track">
                          <div className="h-full rounded-[3px] bg-bar" style={{ width: v == null ? 0 : `${v}%` }} />
                        </div>
                      </div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
          <BandRow span={areas.length + 1}>Facts · the evidence</BandRow>
          {FACT_ROWS.map((row) => (
            <tr key={row.label}>
              <th scope="row" className={`${stickyTh} border-b border-rule px-5 py-[13px] text-sm font-medium text-ink2`}>
                {row.label}
              </th>
              {areas.map((a) => (
                <td key={a.area_id} className="border-b border-rule px-[18px] py-[13px] font-mono text-sm text-ink">
                  {row.value(a)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BandRow({ span, accent, children }: { span: number; accent?: boolean; children: React.ReactNode }) {
  return (
    <tr>
      <td
        colSpan={span}
        className={`bg-card2 px-5 py-[11px] font-mono text-[11px] uppercase tracking-[.1em] ${accent ? "text-accent" : "text-muted"}`}
      >
        {children}
      </td>
    </tr>
  );
}
