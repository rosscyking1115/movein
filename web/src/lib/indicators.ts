import type { Area, ComponentKey } from "./types";
import { epcColor, epcText } from "./epc";
import { km, rate, ratingOrDash, rentPerMonth, score as fmtScore } from "./format";

// Indicator definitions for the area "schedule": each score is paired with the
// figure behind it and an honest, neutral sentence. Sentences describe relative
// position around the documented midpoint, never a percentile claim or verdict.

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
    measure: "Local-authority average rent",
    footnote: 1,
    factLabel: "Local-authority average rent",
    factValue: (a) => rentPerMonth(a.official_rent_monthly_gbp),
    high: "The official local-authority rent context is below the typical-area midpoint.",
    low: "The official local-authority rent context is above the typical-area midpoint.",
  },
  {
    key: "safety_score",
    name: "Recorded crime",
    priorityLabel: "Lower crime",
    measure: "Recorded crime rate",
    footnote: 2,
    factLabel: "Monthly crimes per 1,000 residents",
    factValue: (a) => rate(a.crime_rate_per_1000),
    high: "The recorded-crime rate is below the typical-area midpoint — an indicator, not a label.",
    low: "The recorded-crime rate is above the typical-area midpoint — an indicator, not a label.",
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
    high: "The median EPC band is at or above the D midpoint used by this indicator.",
    low: "The median EPC band is below the D midpoint used by this indicator.",
  },
  {
    key: "flood_score",
    name: "Flood resilience",
    priorityLabel: "Flood resilience",
    measure: "Environment Agency flood zones (England)",
    footnote: 4,
    factLabel: "Flood risk band",
    factValue: (a) => a.flood_risk_flag ?? "—",
    high: "The covered flood-zone share is below the indicator midpoint.",
    low: "The covered flood-zone share is above the indicator midpoint.",
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
    high: "Amenity and station access is above the typical-area midpoint.",
    low: "Amenity and station access is below the typical-area midpoint.",
  },
];

export const SOURCE_NOTES: { no: number; text: string }[] = [
  { no: 1, text: "Average rent is local-authority context from the ONS Price Index of Private Rents; sale prices are MSOA-level HM Land Registry context." },
  { no: 2, text: "Crime is a monthly Police.uk recorded-crime rate using the compatible ONS mid-2024 MSOA population denominator." },
  { no: 3, text: "Energy rating from the EPC Register (median domestic certificate)." },
  { no: 4, text: "Environment Agency and Planning Data flood coverage is England-only here; Wales is shown as not covered, never as low risk." },
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
      plain: has
        ? (s >= 50 ? d.high : d.low)
        : d.key === "flood_score" && area.flood_source_status === "not_covered"
          ? "This source does not cover Wales, so no flood score is assigned."
          : "We don't yet hold this indicator for this area.",
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

export const RENT_LABELS: { key: keyof Area; label: string }[] = [
  { key: "rent_1bed_gbp", label: "1 bed" },
  { key: "rent_2bed_gbp", label: "2 bed" },
  { key: "rent_3bed_gbp", label: "3 bed" },
  { key: "rent_4plus_gbp", label: "4+ bed" },
];

export function factRows(area: Area): { label: string; value: string }[] {
  const crimePeriod =
    area.crime_period_start && area.crime_period_end
      ? `${area.crime_period_start} to ${area.crime_period_end}`
      : "—";
  const crimePopulation =
    area.crime_population_denominator == null
      ? "—"
      : `${area.crime_population_denominator.toLocaleString("en-GB")}${
          area.crime_population_reference_date
            ? ` (reference ${area.crime_population_reference_date})`
            : ""
        }`;
  return [
    ...(area.nearest_city
      ? [{ label: `${area.nearest_city} city centre`, value: km(area.distance_to_city_km) }]
      : []),
    { label: "Median sale price", value: area.median_sale_price_gbp == null ? "—" : `£${area.median_sale_price_gbp.toLocaleString("en-GB")}` },
    { label: "Monthly crime per 1,000", value: rate(area.crime_rate_per_1000) },
    { label: "Recorded-crime period", value: crimePeriod },
    { label: "Crime population denominator", value: crimePopulation },
    { label: "Median EPC", value: ratingOrDash(area.epc_median_rating) },
    {
      label: "Flood risk",
      value: area.flood_source_status === "not_covered" ? "Not covered" : area.flood_risk_flag ?? "—",
    },
    { label: "Nearest station", value: km(area.nearest_station_km) },
    { label: "Nearest supermarket", value: km(area.nearest_supermarket_km) },
    { label: "Nearest GP", value: km(area.nearest_gp_km) },
    { label: "Nearest school", value: km(area.nearest_school_km) },
    { label: "Nearest greenspace", value: km(area.nearest_greenspace_km) },
  ];
}
