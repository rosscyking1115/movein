import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-[640px] px-6 py-24 text-center">
      <div className="font-mono text-xs uppercase tracking-[.18em] text-accent">404</div>
      <h1 className="mt-3 font-display text-[clamp(34px,5vw,52px)] font-bold leading-[1.05] text-ink">
        We couldn&rsquo;t find that area
      </h1>
      <p className="mt-3 text-[17px] leading-[1.6] text-ink2">
        It may be outside our coverage (England &amp; Wales only), or the link is
        stale. Try a postcode or browse by your priorities.
      </p>
      <div className="mt-6 flex justify-center gap-4 text-sm font-semibold">
        <Link href="/" className="text-accent hover:underline">Home</Link>
        <Link href="/search" className="text-accent hover:underline">Search areas</Link>
        <Link href="/rankings" className="text-accent hover:underline">Rankings</Link>
      </div>
    </div>
  );
}
