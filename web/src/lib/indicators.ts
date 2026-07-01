import type { Area, ComponentKey } from "./types";
import { epcColor, epcText } from "./epc";
import { km, rate, ratingOrDash, rentPerMonth, score as fmtScore } from "./format";

// Indicator definitions for the area "schedule": each score is paired with the
// figure behind it and an honest, neutral sentence. Sentences describe relative
// position ("lower/higher than most areas"), never a verdict.

export interface ReceiptRow {
  key: ComponentKey;
  /** chip label used by the priority rail */
  priorityLabel: string;
  name: string;
  measure: string;
  footnote: number;
  plain: string;
  hasData: boolean;
  score: number | null;
  scoreText: string;
  barWidth: string; // e.g. "72%"
  percentileTick: string;
  factLabel: string;
  factValue: string;
  isEpc: boolean;
  epcColor: string | null;
  epcText: string;
}

interface Def {
  key: ComponentKey;
  name: string;
  priorityLabel: string;
  measure: string;
  footnote: number;
  factLabel: string;
  factValue: (a: Area) => string;
  isEpc?: boolean;
  high: string;
  low: string;
}

const DEFS: Def[] = [
  {
    key: "affordability_score",
    name: "Affordability",
    priorityLabel: "Budget",
    measure: "Typical rent & sale price",
    footnote: 1,
    factLabel: "Typical monthly rent",
    factValue: (a) => rentPerMonth(a.official_rent_monthly_gbp),
    high: "Housing costs here are lower than in most England & Wales neighbourhoods.",
    low: "Housing costs here run higher than in most neighbourhoods.",
  },
  {
    key: "safety_score",
    name: "Safety",
    priorityLabel: "Lower crime",
    measure: "Recorded crime rate",
    footnote: 2,
    factLabel: "Crimes per 1,000 residents",
    factValue: (a) => rate(a.crime_rate_per_1000),
    high: "Recorded crime is lower than in most areas — shown as a rate, not a label.",
    low: "Recorded crime is higher than in most areas — shown as a rate, not a label.",
  },
  {
    key: "energy_score",
    name: "Energy efficiency",
    priorityLabel: "Energy bills",
    measure: "Median EPC rating",
    footnote: 3,
    factLabel: "Median EPC band",
    factValue: (a) => ratingOrDash(a.epc_median_rating),
    isEpc: true,
    high: "Homes here tend to be more energy-efficient than average, easing running costs.",
    low: "Homes here tend to be less energy-efficient than average.",
  },
  {
    key: "flood_score",
    name: "Flood resilience",
    priorityLabel: "Flood resilience",
    measure: "Environment Agency flood risk",
    footnote: 4,
    factLabel: "Flood risk band",
    factValue: (a) => a.flood_risk_flag ?? "—",
    high: "Flood risk here is lower than in most areas.",
    low: "Flood risk here is higher than in most areas.",
  },
  {
    key: "convenience_score",
    name: "Getting around",
    priorityLabel: "Getting around",
    measure: "Walkable amenities & transport",
    footnote: 5,
    factLabel: "Walkable amenities",
    factValue: (a) =>
      a.walkable_amenity_count == null ? "—" : `${a.walkable_amenity_count} within reach`,
    high: "Shops, services and transport are more within reach than in most areas.",
    low: "Day-to-day amenities are less within reach than in most areas.",
  },
];

export const SOURCE_NOTES: { no: number; text: string }[] = [
  { no: 1, text: "Rent from the ONS Price Index of Private Rents; sale prices from HM Land Registry." },
  { no: 2, text: "Crime from Police.uk open data (street-level, rate per 1,000 residents)." },
  { no: 3, text: "Energy rating from the EPC Register (median domestic certificate)." },
  { no: 4, text: "Flood risk from the Environment Agency / planning.data.gov.uk." },
  { no: 5, text: "Amenities and transport from OpenStreetMap." },
];

export function buildReceiptRows(area: Area): ReceiptRow[] {
  return DEFS.map((d) => {
    const s = area[d.key];
    const has = s != null;
    return {
      key: d.key,
      priorityLabel: d.priorityLabel,
      name: d.name,
      measure: d.measure,
      footnote: d.footnote,
      plain: has ? (s >= 50 ? d.high : d.low) : "We don't yet hold this indicator for this area.",
      hasData: has,
      score: s,
      scoreText: fmtScore(s),
      barWidth: has ? `${Math.max(0, Math.min(100, s))}%` : "0%",
      percentileTick: has ? (s >= 55 ? "Above the typical area" : s <= 45 ? "Below the typical area" : "About typical") : "",
      factLabel: d.factLabel,
      factValue: d.factValue(area),
      isEpc: Boolean(d.isEpc),
      epcColor: d.isEpc ? epcColor(area.epc_median_rating) : null,
      epcText: d.isEpc ? epcText(area.epc_median_rating) : "#ffffff",
    };
  });
}

/** Three-bar confidence indicator: how many bars are filled. */
export function confidenceFill(level: string | null | undefined): number {
  switch ((level ?? "").toLowerCase()) {
    case "high":
      return 3;
    case "medium":
      return 2;
    default:
      return 1;
  }
}

export const RENT_LABELS: { key: keyof Area; label: string }[] = [
  { key: "rent_1bed_gbp", label: "1 bed" },
  { key: "rent_2bed_gbp", label: "2 bed" },
  { key: "rent_3bed_gbp", label: "3 bed" },
  { key: "rent_4plus_gbp", label: "4+ bed" },
];

export function factRows(area: Area): { label: string; value: string }[] {
  return [
    ...(area.nearest_city
      ? [{ label: `${area.nearest_city} city centre`, value: km(area.distance_to_city_km) }]
      : []),
    { label: "Median sale price", value: area.median_sale_price_gbp == null ? "—" : `£${area.median_sale_price_gbp.toLocaleString("en-GB")}` },
    { label: "Crime per 1,000", value: rate(area.crime_rate_per_1000) },
    { label: "Median EPC", value: ratingOrDash(area.epc_median_rating) },
    { label: "Flood risk", value: area.flood_risk_flag ?? "—" },
    { label: "Nearest station", value: km(area.nearest_station_km) },
    { label: "Nearest supermarket", value: km(area.nearest_supermarket_km) },
    { label: "Nearest GP", value: km(area.nearest_gp_km) },
    { label: "Nearest school", value: km(area.nearest_school_km) },
    { label: "Nearest greenspace", value: km(area.nearest_greenspace_km) },
  ];
}
