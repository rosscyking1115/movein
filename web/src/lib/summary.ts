import type { Area } from "./types";
import { rate, rentPerMonth, score } from "./format";

// A single citable sentence leading each area page (and its meta description) —
// the answer an AI Overview or snippet can lift verbatim. Indicator framing only.

function band(overall: number | null): string {
  if (overall == null) return "an England & Wales";
  if (overall >= 75) return "a higher-scoring";
  if (overall >= 55) return "a mid-scoring";
  if (overall >= 35) return "a lower-mid-scoring";
  return "a lower-scoring";
}

export function answerSentence(area: Area): string {
  const place = [area.local_authority_name, area.region]
    .filter(Boolean)
    .join(", ");
  const where = place ? ` in ${place}` : "";
  const facts: string[] = [];
  if (area.official_rent_monthly_gbp != null)
    facts.push(`official local-authority rent ${rentPerMonth(area.official_rent_monthly_gbp)}`);
  if (area.crime_rate_per_1000 != null)
    facts.push(`${rate(area.crime_rate_per_1000)} crimes per 1,000 residents`);
  if (area.epc_median_rating)
    facts.push(`median EPC ${area.epc_median_rating}`);
  const tail = facts.length ? ` — ${facts.join(", ")}.` : ".";

  return (
    `${area.area_name} is ${band(area.overall_score)} neighbourhood${where}, ` +
    `scoring ${score(area.overall_score)}/100 overall on our affordability, recorded-crime, ` +
    `energy, flood and convenience indicators${tail}`
  );
}
