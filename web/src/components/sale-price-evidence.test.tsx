import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import type { Area } from "@/lib/types";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

import { AreaDetail } from "./area/AreaDetail";
import { CompareTable } from "./CompareTable";
import { buildReceiptRows, factRows } from "@/lib/indicators";

function area(overrides: Partial<Area>): Area {
  return {
    area_id: "E02000001",
    area_name: "Example area",
    local_authority_name: "Example authority",
    region: "London",
    overall_score: null,
    overall_rank: null,
    match_score: null,
    available_component_count: 0,
    expected_component_count: 5,
    all_component_source_dates_known: false,
    evidence_quality_level: "limited",
    evidence_quality_notes: null,
    why_this_area: null,
    affordability_score: null,
    safety_score: null,
    energy_score: null,
    flood_score: null,
    convenience_score: null,
    official_rent_monthly_gbp: null,
    median_sale_price_gbp: 250000,
    sale_price_reference_year: 2025,
    sales_count_latest_year: 5,
    rent_source_grain: null,
    rent_reference_date: null,
    median_sale_price_confidence: "reliable",
    rent_1bed_gbp: null,
    rent_2bed_gbp: null,
    rent_3bed_gbp: null,
    rent_4plus_gbp: null,
    epc_median_rating: null,
    crime_rate_per_1000: null,
    crime_record_count: null,
    crime_months_observed: null,
    crime_period_start: null,
    crime_period_end: null,
    crime_population_denominator: null,
    crime_population_reference_date: null,
    crime_population_geography: null,
    crime_population_source_name: null,
    flood_risk_flag: null,
    flood_postcode_pct: null,
    flood_source_status: null,
    flood_source_name: null,
    planning_constraint_count: null,
    planning_source_status: null,
    planning_source_name: null,
    walkable_amenity_count: null,
    nearest_station_km: null,
    nearest_supermarket_km: null,
    nearest_gp_km: null,
    nearest_school_km: null,
    nearest_greenspace_km: null,
    latitude: null,
    longitude: null,
    nearest_city: null,
    distance_to_city_km: null,
    ...overrides,
  };
}

function renderAreaFacts(value: Area): string {
  return renderToStaticMarkup(
    <AreaDetail
      rows={buildReceiptRows(value)}
      summary="Area context only, not a valuation."
      rentRows={[]}
      factRows={factRows(value)}
      sources={[]}
      areaId={value.area_id}
    />,
  );
}

describe("sale-price evidence in user-facing surfaces", () => {
  it("renders no-sales and indicative evidence in the comparison table", () => {
    const markup = renderToStaticMarkup(
      <CompareTable
        areas={[
          area({ sales_count_latest_year: 0, median_sale_price_confidence: "none" }),
          area({
            area_id: "E02000002",
            area_name: "Indicative area",
            sales_count_latest_year: 2,
            median_sale_price_confidence: "indicative",
          }),
        ]}
      />,
    );

    expect(markup).toContain("No matched sales");
    expect(markup).toContain("2 matched sales in 2025; indicative");
  });

  it("renders reliable evidence and a safe absent-field fallback in the area fact list", () => {
    expect(renderAreaFacts(area({}))).toContain("5 matched sales in 2025; reliable");

    expect(
      renderAreaFacts(
        area({
          sale_price_reference_year: null,
          sales_count_latest_year: null,
          median_sale_price_confidence: null,
        }),
      ),
    ).toContain("£250,000 · —");
  });
});
