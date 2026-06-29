import Link from "next/link";
import type { Area, ComponentKey } from "@/lib/types";
import { areaSlug } from "@/lib/slug";
import { rentPerMonth, score as fmtScore } from "@/lib/format";

const MINI: { key: ComponentKey; abbr: string }[] = [
  { key: "affordability_score", abbr: "Aff" },
  { key: "safety_score", abbr: "Saf" },
  { key: "energy_score", abbr: "Ene" },
  { key: "flood_score", abbr: "Flo" },
  { key: "convenience_score", abbr: "Get" },
];

// A ranked result row for the hubs (rankings, town). The component mix is shown
// so the ranking is legible, not a black box.
export function AreaCard({ area, rank }: { area: Area; rank?: number }) {
  const shown = area.match_score ?? area.overall_score;
  const href = `/area/${areaSlug(area.area_id, area.area_name)}`;
  return (
    <div className="flex items-center gap-4 rounded-[14px] border border-rule2 bg-card px-[18px] py-4">
      {rank != null && <div className="w-7 flex-shrink-0 font-mono text-sm text-muted">#{rank}</div>}
      <div className="min-w-0 flex-1">
        <Link href={href} className="font-display text-[22px] font-bold leading-[1.1] text-ink hover:text-accent">
          {area.area_name}
        </Link>
        <div className="mt-0.5 text-[13px] text-muted">
          {[area.local_authority_name, area.region].filter(Boolean).join(" · ")}
          {area.official_rent_monthly_gbp != null && (
            <>
              {" · "}
              <span className="font-mono text-ink2">{rentPerMonth(area.official_rent_monthly_gbp)}</span>
            </>
          )}
        </div>
        <div className="mt-2.5 hidden flex-wrap gap-3.5 sm:flex">
          {MINI.map((m) => (
            <div key={m.key} className="min-w-[48px]">
              <div className="mb-[3px] flex justify-between gap-1.5 text-[10px] text-muted">
                <span>{m.abbr}</span>
                <span className="font-mono text-ink2">{fmtScore(area[m.key])}</span>
              </div>
              <div className="h-1 w-full overflow-hidden rounded-[2px] bg-bar-track">
                <div className="h-full rounded-[2px] bg-bar" style={{ width: area[m.key] == null ? 0 : `${area[m.key]}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="flex-shrink-0 text-center">
        <div className="font-mono text-[26px] font-medium leading-none text-ink">{fmtScore(shown)}</div>
        <div className="mt-1 text-[10px] uppercase tracking-[.06em] text-muted">/100</div>
      </div>
      <Link
        href={href}
        aria-label={`Open ${area.area_name}`}
        className="flex h-[38px] w-[38px] flex-shrink-0 items-center justify-center self-center rounded-[8px] border border-rule2 bg-card2 text-ink"
      >
        →
      </Link>
    </div>
  );
}
