// Root route-segment loading UI: shown instantly on navigation while a page's
// server render streams in (area pages fetch from the data API, so the old
// behaviour was a frozen screen). Deliberately light — a ledger-style pulse.
export default function Loading() {
  return (
    <div className="mx-auto flex max-w-[1140px] flex-col items-center px-6 py-[120px]">
      <div className="flex h-7 items-end gap-1.5" aria-hidden>
        {[28, 20, 12].map((h, i) => (
          <span
            key={h}
            className="w-2 animate-pulse rounded-[2px] bg-accent"
            style={{ height: h, animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
      <p className="mt-4 font-mono text-[11px] uppercase tracking-[.14em] text-muted">
        Loading…
      </p>
    </div>
  );
}
