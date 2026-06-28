import type { Metadata } from "next";
import Link from "next/link";
import { getAreaOrNull } from "@/lib/api";
import type { Area } from "@/lib/types";
import { CompareControls } from "@/components/CompareControls";
import { CompareTable } from "@/components/CompareTable";

export const metadata: Metadata = {
  title: "Compare neighbourhoods side by side",
  description:
    "Put up to four England & Wales neighbourhoods side by side — scores and the raw facts behind them: rent, crime, EPC, flood risk and amenities.",
};

type Props = { searchParams: Promise<{ areas?: string }> };

const MAX = 4;

function parseCodes(raw: string | undefined): string[] {
  if (!raw) return [];
  return [...new Set(raw.split(",").map((c) => c.trim().toUpperCase()).filter(Boolean))].slice(0, MAX);
}

export default async function ComparePage({ searchParams }: Props) {
  const codes = parseCodes((await searchParams).areas);
  const fetched = await Promise.all(codes.map((c) => getAreaOrNull(c)));
  const areas = fetched.filter((a): a is Area => a !== null);
  const current = areas.map((a) => ({ area_id: a.area_id, area_name: a.area_name }));

  return (
    <div className="mx-auto max-w-4xl px-5 py-10">
      <header className="mb-6 max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">Compare areas</h1>
        <p className="mt-2 text-ink-muted">
          Add up to four neighbourhoods by postcode and see them side by side —
          scores on top, the facts behind them underneath.
        </p>
      </header>

      <CompareControls current={current} />

      <div className="mt-8">
        {areas.length === 0 ? (
          <div className="rounded-card border border-rule bg-paper-raised px-5 py-10 text-center">
            <p className="text-sm text-ink-muted">
              Add an area above to start comparing, or{" "}
              <Link href="/search" className="text-accent underline">
                browse the rankings
              </Link>{" "}
              first.
            </p>
          </div>
        ) : (
          <CompareTable areas={areas} />
        )}
      </div>

      <p className="mt-8 text-xs text-ink-faint">
        Bold marks the highest score in each row. Facts are shown without a
        winner — area-level indicators only, never a &ldquo;safe&rdquo;/&ldquo;unsafe&rdquo;
        verdict or a property valuation.
      </p>
    </div>
  );
}
