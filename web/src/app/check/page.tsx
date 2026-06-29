import type { Metadata } from "next";
import { CheckClient } from "@/components/CheckClient";

export const metadata: Metadata = {
  title: "Check a listing — is the area good and the price fair?",
  description:
    "Paste a postcode, bedrooms and the asking rent or price. We band it against the local typical and show the full area receipt. Manual entry, no portal scraping.",
};

export default function CheckPage() {
  return (
    <div className="mx-auto max-w-[1140px] px-6 pb-[70px] pt-[34px]">
      <header className="mb-7 max-w-[640px]">
        <h1 className="font-display text-[clamp(34px,4.6vw,52px)] font-bold leading-[1.05] text-ink">
          Does this listing&rsquo;s price stack up?
        </h1>
        <p className="mt-2 text-[17px] text-ink2">
          An area-level sanity check — how an asking price sits against what&rsquo;s
          typical locally. Asking price isn&rsquo;t achieved price; treat this as a
          prompt to look closer, not a valuation.
        </p>
      </header>
      <CheckClient />
    </div>
  );
}
