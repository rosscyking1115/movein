import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getAllAreas } from "@/lib/api";
import { regionSlug, townSlug } from "@/lib/geo";
import { findTownBySlug, rankByOverall } from "@/lib/hubs";
import { AreaCard } from "@/components/AreaCard";
import { JsonLd } from "@/components/JsonLd";
import { rankingJsonLd } from "@/lib/structured-data";
import { areaSlug } from "@/lib/slug";

export const revalidate = 86400;

type Props = { params: Promise<{ town: string }> };

async function resolveTown(slug: string) {
  return findTownBySlug(await getAllAreas(), slug);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const town = await resolveTown((await params).town);
  if (!town) return { title: "Area not found", robots: { index: false } };
  const title = `Best areas to live in ${town.name} — rent, crime & scores`;
  return {
    title,
    description: `Every neighbourhood in ${town.name} ranked on affordability, safety, energy, flood risk and convenience, with the rent, crime and amenity facts behind each score.`,
    alternates: { canonical: `/town/${townSlug(town.name)}` },
  };
}

export default async function TownPage({ params }: Props) {
  const town = await resolveTown((await params).town);
  if (!town) notFound();

  const ranked = rankByOverall(town.areas);

  return (
    <div className="mx-auto max-w-[1140px] px-6 pb-[70px] pt-[34px]">
      <nav className="mb-6 font-mono text-xs text-muted">
        <Link href="/" className="hover:text-ink">Home</Link>
        <span className="mx-2">/</span>
        <Link href="/rankings" className="hover:text-ink">Rankings</Link>
        {town.region && (
          <>
            <span className="mx-2">/</span>
            <Link href={`/rankings/${regionSlug(town.region)}`} className="hover:text-ink">
              {town.region}
            </Link>
          </>
        )}
        <span className="mx-2">/</span>
        <span className="text-ink">{town.name}</span>
      </nav>

      <header className="mb-8 max-w-[620px]">
        <h1 className="font-display text-[clamp(34px,4.6vw,52px)] font-bold leading-[1.05] text-ink">
          Best areas to live in {town.name}
        </h1>
        <p className="mt-2 text-[17px] text-ink2">
          {ranked.length.toLocaleString("en-GB")} neighbourhood
          {ranked.length === 1 ? "" : "s"} in {town.name}
          {town.region ? `, ${town.region}` : ""}, ranked by overall indicator
          score.
        </p>
        <Link
          href={`/rent/${townSlug(town.name)}`}
          className="mt-3 inline-block text-sm font-medium text-accent hover:underline"
        >
          See rent prices in {town.name} by bedroom →
        </Link>
      </header>

      <div className="space-y-2">
        {ranked.map((area, i) => (
          <AreaCard key={area.area_id} area={area} rank={i + 1} />
        ))}
      </div>

      <JsonLd
        data={rankingJsonLd({
          title: `Best areas to live in ${town.name}`,
          path: `/town/${townSlug(town.name)}`,
          crumbs: [
            { name: "Home", path: "" },
            { name: "Rankings", path: "/rankings" },
            ...(town.region
              ? [{ name: town.region, path: `/rankings/${regionSlug(town.region)}` }]
              : []),
            { name: town.name, path: `/town/${townSlug(town.name)}` },
          ],
          items: ranked.map((a) => ({
            name: a.area_name,
            path: `/area/${areaSlug(a.area_id, a.area_name)}`,
          })),
        })}
      />
    </div>
  );
}
