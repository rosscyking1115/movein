import Link from "next/link";
import { getMeta } from "@/lib/api";
import { PostcodeBox } from "@/components/PostcodeBox";

export const revalidate = 86400;

async function safeMeta() {
  try {
    return await getMeta();
  } catch {
    return null;
  }
}

// Illustrative rows for the thesis preview (not live data — a worked example).
const HERO_ROWS = [
  { name: "Affordability", fact: "Typical 2-bed rent £1,050/mo", score: 64 },
  { name: "Safety", fact: "58 crimes per 1,000 residents", score: 71 },
  { name: "Energy efficiency", fact: "Median EPC band C", score: 68 },
  { name: "Getting around", fact: "31 amenities within reach", score: 83 },
];

const PRINCIPLES = [
  { no: "01", title: "The figure, beside the score", body: "Every indicator shows the raw number it came from — rent, crime rate, EPC, flood band — so nothing is taken on trust." },
  { no: "02", title: "Indicators, not verdicts", body: "We never call a place good, bad, safe or unsafe. Only higher or lower than other areas, on a neutral scale." },
  { no: "03", title: "Missing data isn't zero", body: "If we don't hold an indicator, we say so and lower confidence — we never score a gap as a zero." },
];

const POPULAR: [string, string][] = [
  ["London", "/rankings/london"],
  ["North West", "/rankings/north-west"],
  ["South East", "/rankings/south-east"],
  ["Yorkshire and The Humber", "/rankings/yorkshire-and-the-humber"],
  ["Wales", "/rankings/wales"],
];

export default async function Home() {
  const meta = await safeMeta();
  const count = meta ? meta.areas.toLocaleString("en-GB") : "7,000+";

  return (
    <div className="mx-auto max-w-[1140px] px-6">
      <section className="max-w-[780px] pb-[26px] pt-[74px]">
        <div className="mb-[22px] font-mono text-xs uppercase tracking-[.18em] text-accent">
          Official open data · England &amp; Wales
        </div>
        <h1 className="mb-[22px] font-display text-[clamp(40px,6.6vw,74px)] font-bold leading-[1.02] tracking-[-.01em] text-ink">
          Every score, shown next&nbsp;to the fact behind&nbsp;it.
        </h1>
        <p className="mb-[34px] max-w-[600px] text-[19px] leading-[1.6] text-ink2">
          MoveIn reads a neighbourhood from official open data and lays it out like
          a surveyor&rsquo;s schedule — five indicators, each beside the figure it
          came from. We show you the evidence; we never tell you a place is
          &ldquo;good&rdquo; or &ldquo;safe.&rdquo;
        </p>
        <PostcodeBox />
        <div className="mt-[11px] text-[13px] text-muted">
          Or browse the{" "}
          <Link href="/rankings" className="font-semibold text-accent underline underline-offset-2">
            area rankings for {count} neighbourhoods
          </Link>
        </div>
      </section>

      {/* Thesis preview */}
      <section className="my-5 grid items-start gap-[18px] [grid-template-columns:repeat(auto-fit,minmax(280px,1fr))]">
        <div className="overflow-hidden rounded-[14px] border border-rule2 bg-card shadow-[0_1px_2px_rgba(20,30,40,.04)]">
          <div className="perforation" />
          <div className="px-[22px] pb-6 pt-5">
            <div className="mb-3.5 font-mono text-[11px] uppercase tracking-[.14em] text-muted">The trade-off receipt</div>
            {HERO_ROWS.map((r) => (
              <div key={r.name} className="flex items-baseline justify-between gap-3.5 border-t border-rule py-[11px]">
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-ink">{r.name}</div>
                  <div className="mt-0.5 text-xs text-muted">{r.fact}</div>
                </div>
                <div className="flex flex-shrink-0 items-center gap-2.5">
                  <div className="h-1.5 w-[74px] overflow-hidden rounded-[3px] bg-bar-track">
                    <div className="h-full rounded-[3px] bg-bar" style={{ width: `${r.score}%` }} />
                  </div>
                  <div className="min-w-[42px] text-right font-mono text-sm font-medium text-ink">{r.score}/100</div>
                </div>
              </div>
            ))}
            <div className="mt-3.5 text-[11px] italic text-muted">
              Sourced from ONS, Police.uk, the EPC Register &amp; the Environment Agency.
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-3.5">
          {PRINCIPLES.map((p) => (
            <div key={p.no} className="rounded-[12px] border border-rule bg-card2 px-5 py-[18px]">
              <div className="mb-[7px] font-mono text-xs text-accent">{p.no}</div>
              <div className="font-semibold text-ink">{p.title}</div>
              <p className="mt-1.5 text-sm leading-[1.5] text-ink2">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="flex flex-wrap items-center gap-2 py-10">
        <span className="mr-1 text-[13px] text-muted">Popular right now:</span>
        {POPULAR.map(([label, href]) => (
          <Link
            key={href}
            href={href}
            className="rounded-full border border-rule2 bg-card px-3 py-1.5 text-[13px] text-ink2 hover:text-ink"
          >
            {label}
          </Link>
        ))}
        <Link href="/methodology" className="ml-1 text-[13px] font-semibold text-accent hover:underline">
          How we score →
        </Link>
      </section>
    </div>
  );
}
