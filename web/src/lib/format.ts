// Display formatting. Numbers read like a ledger: explicit units, no false precision.

const gbp0 = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

export function gbp(value: number | null | undefined): string {
  return value == null ? "—" : gbp0.format(value);
}

/** Monthly rent, e.g. "£1,450/mo". */
export function rentPerMonth(value: number | null | undefined): string {
  return value == null ? "—" : `${gbp0.format(value)}/mo`;
}

export function km(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value < 1) return `${Math.round(value * 1000)} m`;
  return `${value.toFixed(1)} km`;
}

export function score(value: number | null | undefined): string {
  return value == null ? "—" : Math.round(value).toString();
}

export function pct(value: number | null | undefined): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(0)}%`;
}

export function rate(value: number | null | undefined): string {
  return value == null ? "—" : value.toFixed(1);
}

export function ratingOrDash(value: string | null | undefined): string {
  return value && value.trim() ? value : "—";
}

/** Sample and period context required beside an area-level sale-price median. */
export function salePriceEvidence(
  salesCount: number | null | undefined,
  referenceYear: number | null | undefined,
  confidence: string | null | undefined,
): string {
  if (salesCount == null) return "—";
  if (salesCount === 0) return "No matched sales";
  const period = referenceYear == null ? "" : ` in ${referenceYear}`;
  const label = confidence ? `; ${confidence}` : "";
  return `${salesCount.toLocaleString("en-GB")} matched sales${period}${label}`;
}

/** The complete, display-safe area sale-price context for public surfaces. */
export function salePriceWithEvidence(
  salePrice: number | null | undefined,
  salesCount: number | null | undefined,
  referenceYear: number | null | undefined,
  confidence: string | null | undefined,
): string {
  const evidence = salePriceEvidence(salesCount, referenceYear, confidence);

  if (salesCount === 0) return evidence;

  const price = gbp(salePrice);
  if (price === "—") return evidence;

  return `${price} · ${evidence}`;
}
