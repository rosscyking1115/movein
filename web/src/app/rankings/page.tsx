import type { Metadata } from "next";
import Link from "next/link";
import { getAllAreas } from "@/lib/api";
import { REGIONS, regionSlug } from "@/lib/geo";
import { areasInRegion, averageScore } from "@/lib/hubs";
import { score } from "@/lib/format";
import type { Area } from "@/lib/types";

export const revalidate = 86400;

export const metadata: Metadata = {
  title: "Neighbourhood rankings by region",
  description:
    "Browse ranked neighbourhoods across the ten regions of England & Wales by our affordability, safety, energy, flood and convenience indicators.",
};

export default async function RankingsIndex() {
  let all: Area[] = [];
  try {
    all = await getAllAreas();
  } catch {
    all = [];
  }

  const regions = REGIONS.map((name) => {
    const areas = areasInRegion(all, name);
    return { name, count: areas.length, avg: averageScore(areas) };
  });

  return (
    <div className="mx-auto max-w-[1140px] px-6 pb-[70px] pt-[34px]">
      <header className="mb-8 max-w-[620px]">
        <div className="mb-3 font-mono text-xs uppercase tracking-[.18em] text-accent">Rankings</div>
        <h1 className="font-display text-[clamp(34px,4.6vw,52px)] font-bold leading-[1.05] text-ink">
          Rankings by region
        </h1>
        <p className="mt-2 text-[17px] text-ink2">
          A starting point, not a league table. Pick a region to see its
          best-scoring neighbourhoods and a breakdown by local authority.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2">
        {regions.map((r) => (
          <Link
            key={r.name}
            href={`/rankings/${regionSlug(r.name)}`}
            className="flex items-center justify-between rounded-[14px] border border-rule2 bg-card px-5 py-4 hover:border-accent-line"
          >
            <div>
              <div className="font-display text-xl font-bold text-ink">{r.name}</div>
              <div className="text-xs text-muted">{r.count.toLocaleString("en-GB")} areas</div>
            </div>
            <div className="text-right">
              <div className="font-mono text-xl font-medium text-ink">{score(r.avg)}</div>
              <div className="text-[10px] uppercase tracking-[.06em] text-muted">avg</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
