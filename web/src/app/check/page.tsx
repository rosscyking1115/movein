import type { Metadata } from "next";
import { CheckClient } from "@/components/CheckClient";

export const metadata: Metadata = {
  title: "Check a listing — is the area good and the price fair?",
  description:
    "Paste a postcode, bedrooms and the asking rent or price. We band it against the local typical and show the full area receipt. Manual entry, no portal scraping.",
};

export default function CheckPage() {
  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <header className="mb-8 max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">Check a listing</h1>
        <p className="mt-2 text-ink-muted">
          Enter the details from any rental or sale listing. We resolve the
          neighbourhood, band the price against our open-data local typical, and
          show you the area receipt behind it.
        </p>
      </header>
      <CheckClient />
    </div>
  );
}
