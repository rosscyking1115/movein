import Link from "next/link";
import { getMeta } from "@/lib/api";
import { PostcodeBox } from "@/components/PostcodeBox";

// SSG home; revalidate daily so the area count tracks data refreshes.
export const revalidate = 86400;

async function safeMeta() {
  try {
    return await getMeta();
  } catch {
    return null;
  }
}

export default async function Home() {
  const meta = await safeMeta();
  const areaCount = meta ? meta.areas.toLocaleString("en-GB") : "7,000+";

  return (
    <div className="mx-auto max-w-5xl px-5">
      <section className="py-16 sm:py-24">
        <p className="text-sm font-medium text-accent">
          {areaCount} England &amp; Wales neighbourhoods · official open data
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Decide where to live with the fact behind every score.
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-ink-muted">
          Affordability, safety, energy, flood risk and convenience — each shown
          beside the raw number it came from. Set your own priorities. We give you
          indicators, never a &ldquo;safe&rdquo; or &ldquo;unsafe&rdquo; verdict.
        </p>
        <div className="mt-8">
          <PostcodeBox />
        </div>
        <div className="mt-4 flex gap-4 text-sm">
          <Link href="/search" className="font-medium text-accent hover:underline">
            Rank areas by your priorities →
          </Link>
          <Link href="/check" className="font-medium text-accent hover:underline">
            Check a listing →
          </Link>
        </div>
      </section>

      <section className="grid gap-6 border-t border-rule py-12 sm:grid-cols-3">
        {[
          {
            title: "The trade-off receipt",
            body: "Every area page pairs each score with the fact behind it — rent, crime rate, EPC, flood risk, nearest amenities — so a number is never trusted on its own.",
          },
          {
            title: "Your priorities, your ranking",
            body: "Move five sliders and the whole list re-ranks instantly. The overall score is just a weighted average of the things you said you care about.",
          },
          {
            title: "Open data, no scraping",
            body: "Built from Land Registry, ONS, EPC, police, Environment Agency and more. The listing checker is manual entry — we never scrape or store portal listings.",
          },
        ].map((c) => (
          <div key={c.title}>
            <h2 className="font-semibold">{c.title}</h2>
            <p className="mt-2 text-sm text-ink-muted">{c.body}</p>
          </div>
        ))}
      </section>

      <section className="border-t border-rule py-12">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="max-w-xl text-sm text-ink-muted">
            How the scoring works, where every number comes from, and why we show
            uncertainty instead of hiding it.
          </p>
          <Link
            href="/methodology"
            className="rounded-md border border-rule px-4 py-2 text-sm font-medium hover:border-rule-strong"
          >
            Read the methodology
          </Link>
        </div>
      </section>
    </div>
  );
}
