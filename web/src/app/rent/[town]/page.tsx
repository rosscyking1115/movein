import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getAllAreas } from "@/lib/api";
import { regionSlug, townSlug } from "@/lib/geo";
import { averageField, findTownBySlug } from "@/lib/hubs";
import { rentPerMonth } from "@/lib/format";
import { areaSlug } from "@/lib/slug";
import { JsonLd } from "@/components/JsonLd";
import { rankingJsonLd } from "@/lib/structured-data";

export const revalidate = 86400;

type Props = { params: Promise<{ town: string }> };

const BEDS: { key: "rent_1bed_gbp" | "rent_2bed_gbp" | "rent_3bed_gbp" | "rent_4plus_gbp"; label: string }[] = [
  { key: "rent_1bed_gbp", label: "1 bed" },
  { key: "rent_2bed_gbp", label: "2 bed" },
  { key: "rent_3bed_gbp", label: "3 bed" },
  { key: "rent_4plus_gbp", label: "4+ bed" },
];

async function resolveTown(slug: string) {
  return findTownBySlug(await getAllAreas(), slug);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const town = await resolveTown((await params).town);
  if (!town) return { title: "Area not found", robots: { index: false } };
  const avg2 = averageField(town.areas, "rent_2bed_gbp");
  const title = `Rent in ${town.name} — average prices by bedroom`;
  return {
    title,
    description:
      `Average private rents in ${town.name} by bedroom count` +
      (avg2 ? `, around ${rentPerMonth(avg2)} for a 2-bed` : "") +
      `. Per-neighbourhood rents from official ONS data.`,
    alternates: { canonical: `/rent/${townSlug(town.name)}` },
  };
}

export default async function RentTownPage({ params }: Props) {
  const town = await resolveTown((await params).town);
  if (!town) notFound();

  const averages = BEDS.map((b) => ({ ...b, avg: averageField(town.areas, b.key) }));
  // Rank areas by their typical (all-bed) rent, cheapest first.
  const ranked = [...town.areas].sort(
    (a, b) => (a.official_rent_monthly_gbp ?? Infinity) - (b.official_rent_monthly_gbp ?? Infinity),
  );

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
        <Link href={`/town/${townSlug(town.name)}`} className="hover:text-ink">{town.name}</Link>
        <span className="mx-2">/</span>
        <span className="text-ink">Rent</span>
      </nav>

      <header className="mb-8 max-w-[620px]">
        <h1 className="font-display text-[clamp(34px,4.6vw,52px)] font-bold leading-[1.05] text-ink">
          Rent in {town.name}
        </h1>
        <p className="mt-2 text-[17px] text-ink2">
          Average monthly private rents across {ranked.length} neighbourhood
          {ranked.length === 1 ? "" : "s"} in {town.name}, by bedroom count.
          Figures are area-level ONS estimates — a benchmark, not a quote.
        </p>
      </header>

      {/* LA-level averages per bedroom. */}
      <section className="mb-10 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {averages.map((a) => (
          <div key={a.key} className="rounded-card border border-rule bg-card px-4 py-3">
            <div className="text-xs uppercase tracking-wide text-muted">{a.label}</div>
            <div className="tnum mt-1 text-xl font-semibold">{rentPerMonth(a.avg)}</div>
          </div>
        ))}
      </section>

      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted">
          By neighbourhood — cheapest first
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] border-collapse text-sm">
            <thead>
              <tr className="rule-b text-muted">
                <th className="px-3 py-2 text-left font-normal">Neighbourhood</th>
                {BEDS.map((b) => (
                  <th key={b.key} className="px-3 py-2 text-right font-normal">{b.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ranked.map((area) => (
                <tr key={area.area_id} className="rule-b">
                  <td className="px-3 py-2">
                    <Link
                      href={`/area/${areaSlug(area.area_id, area.area_name)}`}
                      className="hover:text-accent"
                    >
                      {area.area_name}
                    </Link>
                  </td>
                  {BEDS.map((b) => (
                    <td key={b.key} className="tnum px-3 py-2 text-right">
                      {rentPerMonth(area[b.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="mt-6 text-sm">
        <Link href={`/town/${townSlug(town.name)}`} className="font-medium text-accent hover:underline">
          See the full area scores for {town.name} →
        </Link>
      </p>

      <JsonLd
        data={rankingJsonLd({
          title: `Rent in ${town.name}`,
          path: `/rent/${townSlug(town.name)}`,
          crumbs: [
            { name: "Home", path: "" },
            { name: "Rankings", path: "/rankings" },
            ...(town.region
              ? [{ name: town.region, path: `/rankings/${regionSlug(town.region)}` }]
              : []),
            { name: town.name, path: `/town/${townSlug(town.name)}` },
            { name: "Rent", path: `/rent/${townSlug(town.name)}` },
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
