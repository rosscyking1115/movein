import type { Metadata } from "next";
import Link from "next/link";
import { notFound, permanentRedirect } from "next/navigation";
import { getAreaOrNull } from "@/lib/api";
import { regionSlug, townSlug } from "@/lib/geo";
import { areaSlug, msoaFromSlug } from "@/lib/slug";
import { completeness } from "@/lib/quality";
import { answerSentence } from "@/lib/summary";
import { areaJsonLd } from "@/lib/structured-data";
import { AreaReceipt } from "@/components/AreaReceipt";
import { JsonLd } from "@/components/JsonLd";
import type { Area } from "@/lib/types";

// ISR: pre-render on first request, then serve cached for a day. Long-tail
// areas generate on demand (dynamicParams defaults to true).
export const revalidate = 86400;

type Props = { params: Promise<{ slug: string }> };

const load = (slug: string): Promise<Area | null> => getAreaOrNull(msoaFromSlug(slug));

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const area = await load(slug);
  if (!area) return { title: "Area not found", robots: { index: false, follow: false } };

  const { indexable } = completeness(area);
  const title = `${area.area_name} — area score, rent & crime`;
  const canonical = `/area/${areaSlug(area.area_id, area.area_name)}`;
  return {
    title,
    description: answerSentence(area),
    alternates: { canonical },
    openGraph: { title, description: answerSentence(area), url: canonical },
    // Thin-content discipline: sparse areas stay out of the index until they fill in.
    robots: indexable
      ? { index: true, follow: true }
      : { index: false, follow: true },
  };
}

export default async function AreaPage({ params }: Props) {
  const { slug } = await params;
  const area = await load(slug);
  if (!area) notFound();

  // Canonicalise: send /area/<code> or a stale name straight to the human slug.
  const canonical = areaSlug(area.area_id, area.area_name);
  if (slug !== canonical) permanentRedirect(`/area/${canonical}`);

  return (
    <article className="mx-auto max-w-3xl px-5 py-10">
      <nav className="mb-6 text-xs text-ink-muted">
        <Link href="/" className="hover:text-ink">Home</Link>
        <span className="mx-2">/</span>
        <Link href="/search" className="hover:text-ink">Areas</Link>
        <span className="mx-2">/</span>
        <span className="text-ink">{area.area_name}</span>
      </nav>

      <AreaReceipt area={area} />

      <div className="mt-10 rounded-card border border-rule bg-paper-raised p-5">
        <h2 className="text-sm font-semibold">Compare this with somewhere else</h2>
        <p className="mt-1 text-sm text-ink-muted">
          Put {area.area_name} side by side with another area, or rank by your own
          priorities.
        </p>
        <div className="mt-3 flex flex-wrap gap-4 text-sm font-medium text-accent">
          <Link href={`/compare?areas=${area.area_id}`} className="hover:underline">
            Compare {area.area_name} →
          </Link>
          <Link href="/search" className="hover:underline">
            Rank by priorities →
          </Link>
        </div>
      </div>

      {/* Link mesh: area → its town and region hubs (which list the neighbours). */}
      {(area.local_authority_name || area.region) && (
        <nav className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm">
          {area.local_authority_name && (
            <Link
              href={`/town/${townSlug(area.local_authority_name)}`}
              className="text-accent hover:underline"
            >
              Other areas in {area.local_authority_name} →
            </Link>
          )}
          {area.region && (
            <Link
              href={`/rankings/${regionSlug(area.region)}`}
              className="text-accent hover:underline"
            >
              Best areas in {area.region} →
            </Link>
          )}
        </nav>
      )}

      <p className="mt-8 text-xs text-ink-faint">
        Area-level indicators only — not a property valuation, and never a
        &ldquo;safe&rdquo; or &ldquo;unsafe&rdquo; label. See our{" "}
        <Link href="/methodology" className="underline">methodology</Link>.
      </p>

      <JsonLd data={areaJsonLd(area, canonical)} />
    </article>
  );
}
