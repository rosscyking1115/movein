import type { Metadata } from "next";
import Link from "next/link";
import { getMeta } from "@/lib/api";

export const revalidate = 86400;

export const metadata: Metadata = {
  title: "Methodology & data sources",
  description:
    "How MoveIn scores England & Wales neighbourhoods: five 0–100 indicators, a weighted average you control, explicit confidence, and the official open-data sources behind every number.",
};

const INDICATORS: [string, string, string][] = [
  ["Affordability", "ONS · HM Land Registry", "Local rent (overall and per-bedroom) and median sale price, relative to other areas."],
  ["Safety", "Police.uk", "Recorded-crime rate per 1,000 residents. A rate and a caveat — never a safe/unsafe label."],
  ["Energy efficiency", "EPC Register", "Median EPC rating: a proxy for running costs and comfort."],
  ["Flood resilience", "Environment Agency", "Flood-risk data. A resilience indicator, not a property-level survey."],
  ["Getting around", "OpenStreetMap", "Walkable amenity count and distance to the nearest station, supermarket, GP, school and greenspace."],
];

const REFUSALS = [
  "Label an area “safe”, “unsafe”, “good” or “bad”.",
  "Colour scores red-to-green as good/bad — bars stay on a neutral scale.",
  "Score missing data as zero — a gap lowers confidence instead.",
  "Value an individual property — this is area-level guidance only.",
];

const SOURCES: [string, string][] = [
  ["HM Land Registry Price Paid", "Sale prices and market context (England & Wales)."],
  ["ONS Private Rent & House Price", "Official rent levels, including per-bedroom (PIPR)."],
  ["ONS / geography lookup", "Postcode → LSOA / MSOA / local authority / region."],
  ["EPC (GOV.UK)", "Energy efficiency ratings aggregated to area level."],
  ["Police.uk API", "Crime indicator profile by area and month."],
  ["Planning Data API", "Planning constraints and context."],
  ["Environment Agency", "Flood areas and monitoring."],
  ["OpenStreetMap / Overpass", "Amenities, stations, shops, green space."],
];

async function safeMeta() {
  try {
    return await getMeta();
  } catch {
    return null;
  }
}

export default async function MethodologyPage() {
  const meta = await safeMeta();

  return (
    <article className="mx-auto max-w-[780px] px-6 pb-[70px] pt-[34px]">
      <div className="mb-3 font-mono text-xs uppercase tracking-[.18em] text-accent">Methodology</div>
      <h1 className="font-display text-[clamp(34px,5vw,56px)] font-bold leading-[1.05] text-ink">
        How the score is built
      </h1>
      <p className="mt-3 text-[18px] leading-[1.6] text-ink2">
        Five comparable indicators for every neighbourhood (MSOA) in England &amp;
        Wales{meta ? ` — ${meta.areas.toLocaleString("en-GB")} areas` : ""}. Each is
        a 0–100 score where <strong className="text-ink">50 marks the typical area</strong>:
        we clip the extremes (2nd/98th percentile) and stretch the rest so the
        middle of the country sits at 50 and real magnitude is kept. EPC and flood
        use fixed, absolute anchors.
        {meta?.data_vintage ? ` Data vintage: ${meta.data_vintage}.` : ""}
      </p>

      <section className="mt-10">
        {INDICATORS.map(([name, source, body]) => (
          <div key={name} className="grid gap-1 border-t border-rule py-4 sm:grid-cols-[160px_1fr] sm:gap-6">
            <div>
              <div className="font-semibold text-ink">{name}</div>
              <div className="font-mono text-[11px] uppercase tracking-wider text-muted">{source}</div>
            </div>
            <p className="text-[15px] leading-[1.6] text-ink2">{body}</p>
          </div>
        ))}
      </section>

      <section className="mt-8">
        <h2 className="font-display text-2xl font-bold text-ink">The overall score</h2>
        <p className="mt-3 text-[15px] leading-[1.6] text-ink2">
          The overall score is a <strong className="text-ink">weighted geometric mean</strong>{" "}
          of the five indicators — equal weights by default, or whatever priorities
          you set on the <Link href="/search" className="text-accent underline">search page</Link>.
          A geometric mean (rather than a plain average) means one excellent
          indicator can&rsquo;t paper over a poor one — a place that&rsquo;s great on
          energy but unaffordable and flood-prone won&rsquo;t float to the top.
          Missing an indicator? We drop it rather than scoring it zero: missing data
          lowers confidence, it never silently penalises an area.
        </p>
      </section>

      <section className="mt-8 rounded-[16px] border border-accent-line bg-accent-wash p-6">
        <div className="mb-3 font-mono text-[11px] uppercase tracking-[.12em] text-accent">
          What we deliberately don&rsquo;t do
        </div>
        <ul className="space-y-2.5">
          {REFUSALS.map((r) => (
            <li key={r} className="flex gap-2.5 text-[15px] leading-[1.5] text-ink">
              <span className="font-mono text-caution" aria-hidden>✕</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </section>

      <section id="sources" className="mt-10 scroll-mt-20">
        <h2 className="font-display text-2xl font-bold text-ink">Data sources</h2>
        <dl className="mt-4">
          {SOURCES.map(([name, desc]) => (
            <div key={name} className="flex flex-col gap-0.5 border-t border-rule py-3 sm:flex-row sm:justify-between sm:gap-4">
              <dt className="font-semibold text-ink">{name}</dt>
              <dd className="text-sm text-ink2 sm:max-w-sm sm:text-right">{desc}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-xs text-muted">
          Sources are official/open and used under their respective licences. Some
          figures are provisional and subject to revision by the publisher.
        </p>
      </section>
    </article>
  );
}
