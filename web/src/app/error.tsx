"use client";

import { useEffect } from "react";

// App-level error boundary: a friendly, branded page instead of the raw Next.js
// server-error screen when something fails (most often the data API being
// unavailable / cold-starting).
export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // Errors are already logged server-side; nothing to do here.
  }, []);

  return (
    <div className="mx-auto max-w-[640px] px-6 py-24 text-center">
      <div className="font-mono text-xs uppercase tracking-[.18em] text-accent">Something went wrong</div>
      <h1 className="mt-3 font-display text-[clamp(30px,5vw,48px)] font-bold leading-[1.05] text-ink">
        We couldn&rsquo;t load this page
      </h1>
      <p className="mt-3 text-[17px] leading-[1.6] text-ink2">
        The data service may be starting up or briefly unavailable. Give it a
        moment and try again.
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-6 cursor-pointer rounded-[10px] bg-accent px-5 py-2.5 text-sm font-semibold text-white"
      >
        Try again
      </button>
    </div>
  );
}
