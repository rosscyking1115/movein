import type { Metadata } from "next";
import Link from "next/link";
import { getMeta } from "@/lib/api";

export const revalidate = 86400;

export const metadata: Metadata = {
  title: "Methodology & data sources",
  description:
    "How we score England & Wales neighbourhoods: five 0–100 indicators, a weighted average you control, explicit confidence, and the official open-data sources behind every number.",
};

const COMPONENTS = [
  ["Affordability", "ONS private rent (overall and per-bedroom) and Land Registry median sale price, relative to other areas."],
  ["Safety", "Police recorded-crime rates per 1,000 residents. A rate and a caveat — never a safe/unsafe label."],
  ["Energy", "Median EPC rating from GOV.UK energy certificates: a proxy for running costs and comfort."],
  ["Flood", "Environment Agency flood data. Resilience indicator, not a property-level flood survey."],
  ["Convenience", "Walkable amenity count and distance to the nearest station, supermarket, GP, school and greenspace (OpenStreetMap)."],
];

const SOURCES = [
  ["HM Land Registry Price Paid", "Sale prices and market context (England & Wales)."],
  ["ONS Private Rent & House Price statistics", "Official rent levels, including per-bedroom (PIPR)."],
  ["ONS / geography postcode lookup", "Postcode → LSOA / MSOA / local authority / region."],
  ["EPC (GOV.UK)", "Energy efficiency ratings aggregated to area level."],
  ["Police API", "Crime indicator profile by area and month."],
  ["Planning Data API", "Planning constraints and context."],
  ["Environment Agency flood data", "Flood areas and monitoring."],
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
    <article className="mx-auto max-w-3xl px-5 py-10">
      <h1 className="text-3xl font-semibold tracking-tight">Methodology</h1>
      <p className="mt-3 text-ink-muted">
        We turn nine official open-data sources into five comparable indicators
        for every neighbourhood (MSOA) in England &amp; Wales
        {meta ? ` — ${meta.areas.toLocaleString("en-GB")} areas` : ""}. Each
        indicator is a 0–100 percentile rank against all other areas.
        {meta?.data_vintage ? ` Data vintage: ${meta.data_vintage}.` : ""}
      </p>

      <section className="mt-10">
        <h2 className="text-lg font-semibold">The five indicators</h2>
        <dl className="mt-4 space-y-4">
          {COMPONENTS.map(([name, desc]) => (
            <div key={name}>
              <dt className="font-medium">{name}</dt>
              <dd className="text-sm text-ink-muted">{desc}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-semibold">The overall score</h2>
        <p className="mt-3 text-sm text-ink-muted">
          The overall score is a <strong>weighted average</strong> of the five
          indicators — using equal weights by default, or whatever priorities you
          set on the{" "}
          <Link href="/search" className="underline">search page</Link>. If an
          area is missing an indicator, we drop it from the average rather than
          scoring it zero: missing data lowers confidence, it never silently
          penalises an area.
        </p>
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-semibold">What we deliberately don&rsquo;t do</h2>
        <ul className="mt-3 space-y-2 text-sm text-ink-muted">
          <li>• No &ldquo;safe&rdquo; or &ldquo;unsafe&rdquo; verdicts — always the raw rate beside the score.</li>
          <li>• No property valuations — these are area-level indicators, and asking ≠ achieved price.</li>
          <li>• No scraping or storing of portal listings — the listing checker is manual entry against our own open data.</li>
        </ul>
      </section>

      <section id="sources" className="mt-10 scroll-mt-20">
        <h2 className="text-lg font-semibold">Data sources</h2>
        <dl className="mt-4 divide-y divide-rule">
          {SOURCES.map(([name, desc]) => (
            <div key={name} className="flex flex-col gap-0.5 py-3 sm:flex-row sm:justify-between sm:gap-4">
              <dt className="font-medium">{name}</dt>
              <dd className="text-sm text-ink-muted sm:max-w-sm sm:text-right">{desc}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-4 text-xs text-ink-faint">
          Sources are official/open and used under their respective licences.
          Some figures are provisional and subject to revision by the publisher.
        </p>
      </section>
    </article>
  );
}
