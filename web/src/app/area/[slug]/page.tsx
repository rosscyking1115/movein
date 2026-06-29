import type { Metadata } from "next";
import Link from "next/link";
import { notFound, permanentRedirect } from "next/navigation";
import { getAreaOrNull } from "@/lib/api";
import { regionSlug, townSlug } from "@/lib/geo";
import { areaSlug, msoaFromSlug } from "@/lib/slug";
import { completeness } from "@/lib/quality";
import { answerSentence } from "@/lib/summary";
import { areaJsonLd } from "@/lib/structured-data";
import {
  buildReceiptRows,
  confidenceFill,
  factRows as buildFactRows,
  RENT_LABELS,
  SOURCE_NOTES,
} from "@/lib/indicators";
import { rentPerMonth, score as fmtScore } from "@/lib/format";
import { AreaDetail } from "@/components/area/AreaDetail";
import { JsonLd } from "@/components/JsonLd";
import type { Area } from "@/lib/types";

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
    robots: indexable ? { index: true, follow: true } : { index: false, follow: true },
  };
}

export default async function AreaPage({ params }: Props) {
  const { slug } = await params;
  const area = await load(slug);
  if (!area) notFound();

  const canonical = areaSlug(area.area_id, area.area_name);
  if (slug !== canonical) permanentRedirect(`/area/${canonical}`);

  const rows = buildReceiptRows(area);
  const fill = confidenceFill(area.confidence_level);
  const rentRows = RENT_LABELS.map((r) => ({ label: r.label, value: rentPerMonth(area[r.key] as number | null) }));
  const summary = area.why_this_area ?? answerSentence(area);

  return (
    <article className="mx-auto max-w-[1140px] px-6 py-9">
      <nav className="mb-5 flex flex-wrap items-center gap-2 font-mono text-xs text-muted">
        <Link href="/" className="hover:text-ink">England &amp; Wales</Link>
        <span>›</span>
        <span>{area.region}</span>
        <span>›</span>
        <span className="text-ink2">{area.local_authority_name}</span>
      </nav>

      {/* Header block */}
      <div className="flex flex-wrap items-end justify-between gap-x-10 gap-y-7 border-b border-rule2 pb-[26px]">
        <div className="max-w-[560px]">
          <h1 className="font-display text-[clamp(38px,5.4vw,60px)] font-bold leading-[1.04] tracking-[-.01em] text-ink">
            {area.area_name}
          </h1>
          <div className="mt-2.5 text-base text-ink2">
            {[area.local_authority_name, area.region].filter(Boolean).join(" · ")}
          </div>
          <p className="mt-[18px] text-[17px] leading-[1.6] text-ink2">{answerSentence(area)}</p>
        </div>
        <div className="flex items-end gap-[26px]">
          <div>
            <div className="mb-1.5 font-mono text-[11px] uppercase tracking-[.12em] text-muted">Composite</div>
            <div className="flex items-baseline gap-[2px]">
              <span className="font-mono text-[62px] font-medium leading-[.9] tracking-[-.02em] text-ink">
                {fmtScore(area.overall_score)}
              </span>
              <span className="font-mono text-[22px] text-muted">/100</span>
            </div>
            <div className="mt-2 text-[13px] text-ink2">
              Rank <span className="font-mono text-ink">{area.overall_rank?.toLocaleString("en-GB") ?? "—"}</span> of 7,264
            </div>
          </div>
          <div className="border-l border-rule2 pl-6">
            <div className="mb-2 font-mono text-[11px] uppercase tracking-[.12em] text-muted">Confidence</div>
            <div className="flex h-6 items-end gap-1">
              {[24, 18, 12].map((h, i) => (
                <span
                  key={h}
                  className="w-[7px] rounded-[2px]"
                  style={{ height: h, background: i < fill ? "var(--accent)" : "var(--rule2)" }}
                />
              ))}
            </div>
            <div className="mt-2 text-[13px] capitalize text-ink2">{area.confidence_level ?? "low"}</div>
          </div>
        </div>
      </div>

      <AreaDetail
        rows={rows}
        summary={summary}
        rentRows={rentRows}
        factRows={buildFactRows(area)}
        sources={SOURCE_NOTES}
        areaId={area.area_id}
      />

      {/* Mesh links */}
      <div className="mt-[34px] grid gap-[22px] border-t border-rule2 pt-[22px] sm:grid-cols-3">
        <MeshCol title={`Nearby in ${area.local_authority_name ?? "this area"}`}>
          {area.local_authority_name && (
            <MeshLink href={`/town/${townSlug(area.local_authority_name)}`}>
              Other areas in {area.local_authority_name}
            </MeshLink>
          )}
        </MeshCol>
        <MeshCol title="Browse">
          {area.region && (
            <MeshLink href={`/rankings/${regionSlug(area.region)}`}>Best areas in {area.region}</MeshLink>
          )}
          {area.local_authority_name && (
            <MeshLink href={`/rent/${townSlug(area.local_authority_name)}`}>
              Rent in {area.local_authority_name}
            </MeshLink>
          )}
          <MeshLink href="/search">Rank by my priorities</MeshLink>
        </MeshCol>
        <MeshCol title="Checking a listing?">
          <MeshLink href="/check">Check a listing&rsquo;s area &amp; price</MeshLink>
        </MeshCol>
      </div>

      <JsonLd data={areaJsonLd(area, canonical)} />
    </article>
  );
}

function MeshCol({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-[11px] font-mono text-[11px] uppercase tracking-[.1em] text-muted">{title}</div>
      {children}
    </div>
  );
}

function MeshLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="block py-[5px] text-sm text-accent hover:underline">
      {children} →
    </Link>
  );
}
