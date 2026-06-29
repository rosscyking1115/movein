import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getAllAreas, getMeta } from "@/lib/api";
import { REGIONS, regionFromSlug, regionSlug, townSlug } from "@/lib/geo";
import { areasInRegion, rankByOverall, townsInRegion } from "@/lib/hubs";
import { score } from "@/lib/format";
import { AreaCard } from "@/components/AreaCard";
import { JsonLd } from "@/components/JsonLd";
import { rankingJsonLd } from "@/lib/structured-data";
import { areaSlug } from "@/lib/slug";

export const revalidate = 86400;

const TOP_AREAS = 50;

type Props = { params: Promise<{ region: string }> };

// Pre-render all ten region hubs when the API is reachable at build (production,
// API_BASE_URL → live service). When it isn't (local/CI builds decoupled from the
// API), defer to on-demand ISR so the website build stays green on its own.
export async function generateStaticParams() {
  try {
    await getMeta();
  } catch {
    return [];
  }
  return REGIONS.map((r) => ({ region: regionSlug(r) }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const region = regionFromSlug((await params).region);
  if (!region) return { title: "Region not found", robots: { index: false } };
  const title = `Best areas to live in ${region} — ranked`;
  return {
    title,
    description: `Neighbourhoods in ${region} ranked on affordability, safety, energy, flood risk and convenience, each shown with the facts behind the score.`,
    alternates: { canonical: `/rankings/${regionSlug(region)}` },
  };
}

export default async function RegionRanking({ params }: Props) {
  const region = regionFromSlug((await params).region);
  if (!region) notFound();

  const all = await getAllAreas();
  const ranked = rankByOverall(areasInRegion(all, region));
  if (ranked.length === 0) notFound();

  const top = ranked.slice(0, TOP_AREAS);
  const towns = townsInRegion(all, region);

  return (
    <div className="mx-auto max-w-[1140px] px-6 pb-[70px] pt-[34px]">
      <nav className="mb-6 font-mono text-xs text-muted">
        <Link href="/" className="hover:text-ink">Home</Link>
        <span className="mx-2">›</span>
        <Link href="/rankings" className="hover:text-ink">Rankings</Link>
        <span className="mx-2">›</span>
        <span className="text-ink2">{region}</span>
      </nav>

      <header className="mb-8 max-w-[620px]">
        <h1 className="font-display text-[clamp(34px,4.6vw,52px)] font-bold leading-[1.05] text-ink">
          Best areas to live in {region}
        </h1>
        <p className="mt-2 text-[17px] text-ink2">
          {ranked.length.toLocaleString("en-GB")} neighbourhoods ranked by overall
          indicator score. Each score sits beside the fact behind it.
        </p>
      </header>

      {towns.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted">
            By local authority
          </h2>
          <div className="flex flex-wrap gap-2">
            {towns.map((t) => (
              <Link
                key={t.name}
                href={`/town/${townSlug(t.name)}`}
                className="inline-flex items-center gap-2 rounded-full border border-rule bg-card px-3 py-1 text-sm hover:border-rule2"
              >
                {t.name}
                <span className="tnum text-xs text-muted">{score(t.avgScore)}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted">
          Top {top.length} areas
        </h2>
        <div className="space-y-2">
          {top.map((area, i) => (
            <AreaCard key={area.area_id} area={area} rank={i + 1} />
          ))}
        </div>
      </section>

      <JsonLd
        data={rankingJsonLd({
          title: `Best areas to live in ${region}`,
          path: `/rankings/${regionSlug(region)}`,
          crumbs: [
            { name: "Home", path: "" },
            { name: "Rankings", path: "/rankings" },
            { name: region, path: `/rankings/${regionSlug(region)}` },
          ],
          items: top.map((a) => ({
            name: a.area_name,
            path: `/area/${areaSlug(a.area_id, a.area_name)}`,
          })),
        })}
      />
    </div>
  );
}
