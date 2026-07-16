"""Pydantic request/response models — the typed contract for web + mobile."""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Area(BaseModel):
    """One MSOA: scores + the raw facts behind them. match_score is set by /search."""

    model_config = ConfigDict(extra="ignore")

    area_id: str
    area_name: str
    local_authority_name: Optional[str] = None
    region: Optional[str] = None
    overall_score: Optional[float] = None
    overall_rank: Optional[int] = None
    match_score: Optional[float] = None
    available_component_count: Optional[int] = None
    expected_component_count: int = 5
    all_component_source_dates_known: bool = False
    evidence_quality_level: Optional[Literal["strong", "mixed", "limited"]] = None
    evidence_quality_notes: Optional[str] = None
    why_this_area: Optional[str] = None
    affordability_score: Optional[float] = None
    safety_score: Optional[float] = None
    energy_score: Optional[float] = None
    flood_score: Optional[float] = None
    convenience_score: Optional[float] = None
    official_rent_monthly_gbp: Optional[float] = None
    median_sale_price_gbp: Optional[float] = None
    rent_source_grain: Optional[str] = None
    rent_reference_date: Optional[date] = None
    median_sale_price_confidence: Optional[str] = None
    rent_1bed_gbp: Optional[float] = None
    rent_2bed_gbp: Optional[float] = None
    rent_3bed_gbp: Optional[float] = None
    rent_4plus_gbp: Optional[float] = None
    epc_median_rating: Optional[str] = None
    crime_rate_per_1000: Optional[float] = None
    crime_record_count: Optional[int] = None
    crime_months_observed: Optional[int] = None
    crime_period_start: Optional[str] = None
    crime_period_end: Optional[str] = None
    crime_population_denominator: Optional[int] = None
    crime_population_reference_date: Optional[date] = None
    crime_population_geography: Optional[str] = None
    crime_population_source_name: Optional[str] = None
    flood_risk_flag: Optional[str] = None
    flood_postcode_pct: Optional[float] = None
    flood_source_status: Optional[str] = None
    flood_source_name: Optional[str] = None
    planning_constraint_count: Optional[int] = None
    planning_source_status: Optional[str] = None
    planning_source_name: Optional[str] = None
    walkable_amenity_count: Optional[int] = None
    nearest_station_km: Optional[float] = None
    nearest_supermarket_km: Optional[float] = None
    nearest_gp_km: Optional[float] = None
    nearest_school_km: Optional[float] = None
    nearest_greenspace_km: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nearest_city: Optional[str] = None
    distance_to_city_km: Optional[float] = None


class Meta(BaseModel):
    areas: int
    components: list[str]
    default_weights: dict[str, float]
    data_vintage: str
    scoring_contract_version: str
    note: str


class AreaIndexResponse(BaseModel):
    """The whole dataset in one cacheable GET — for clients that group/rank/index
    over all areas (the website's hubs, sitemap, link mesh)."""

    count: int
    data_vintage: str
    areas: list[Area]


class SearchRequest(BaseModel):
    weights: dict[str, float] = Field(
        default_factory=dict,
        description="Component weight per priority (default: all equal).",
    )
    max_rent: Optional[float] = Field(None, description="Filter to areas at/below this monthly rent.")
    regions: Optional[list[str]] = Field(None, description="Restrict to these regions.")
    min_overall: Optional[float] = Field(None, description="Minimum match score.")
    limit: int = Field(25, ge=1, le=200)
    offset: int = Field(0, ge=0)

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, weights: dict[str, float]) -> dict[str, float]:
        from . import scoring

        unknown = set(weights) - set(scoring.COMPONENTS)
        if unknown:
            raise ValueError(f"Unknown scoring components: {', '.join(sorted(unknown))}")
        for value in weights.values():
            if not scoring.MIN_WEIGHT <= value <= scoring.MAX_WEIGHT:
                raise ValueError(
                    f"Weights must be between {scoring.MIN_WEIGHT:g} and {scoring.MAX_WEIGHT:g}."
                )
        return weights


class SearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: list[Area]


class ResolveResponse(BaseModel):
    postcode: str
    msoa_code: str
    msoa_name: Optional[str] = None
    area: Area


class ListingCheckRequest(BaseModel):
    postcode: str
    deal: Literal["rent", "buy"] = "rent"
    bedrooms: Literal["1", "2", "3", "4plus", "any"] = "any"
    asking_gbp: float = Field(gt=0, description="Monthly rent for a rental, or the listed price for a sale.")


class PriceCheck(BaseModel):
    asking_gbp: float
    comparison_gbp: Optional[float] = None
    pct_vs_comparison: Optional[float] = None
    band: str
    basis: str


class ListingCheckResponse(BaseModel):
    postcode: str
    msoa_code: str
    msoa_name: Optional[str] = None
    area: Area
    price: Optional[PriceCheck] = None


class LegacyPriceCheck(BaseModel):
    """Deprecated v1 names retained only on the hidden compatibility route."""

    asking_gbp: float
    local_typical_gbp: Optional[float] = None
    pct_vs_local: Optional[float] = None
    band: str
    basis: str


class LegacyListingCheckResponse(BaseModel):
    postcode: str
    msoa_code: str
    msoa_name: Optional[str] = None
    area: Area
    price: Optional[LegacyPriceCheck] = None
