import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-2xl px-5 py-24 text-center">
      <p className="text-sm font-medium text-accent">404</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">
        We couldn&rsquo;t find that area
      </h1>
      <p className="mt-3 text-ink-muted">
        It may be outside our coverage (England &amp; Wales only), or the link is
        stale. Try a postcode or browse by your priorities.
      </p>
      <div className="mt-6 flex justify-center gap-4 text-sm">
        <Link href="/" className="font-medium text-accent hover:underline">Home</Link>
        <Link href="/search" className="font-medium text-accent hover:underline">Search areas</Link>
      </div>
    </div>
  );
}
