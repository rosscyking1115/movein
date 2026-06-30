"""Pydantic request/response models — the typed contract for web + mobile."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    confidence_level: Optional[str] = None
    why_this_area: Optional[str] = None
    affordability_score: Optional[float] = None
    safety_score: Optional[float] = None
    energy_score: Optional[float] = None
    flood_score: Optional[float] = None
    convenience_score: Optional[float] = None
    official_rent_monthly_gbp: Optional[float] = None
    median_sale_price_gbp: Optional[float] = None
    rent_1bed_gbp: Optional[float] = None
    rent_2bed_gbp: Optional[float] = None
    rent_3bed_gbp: Optional[float] = None
    rent_4plus_gbp: Optional[float] = None
    epc_median_rating: Optional[str] = None
    crime_rate_per_1000: Optional[float] = None
    flood_risk_flag: Optional[str] = None
    planning_constraint_count: Optional[int] = None
    walkable_amenity_count: Optional[int] = None
    nearest_station_km: Optional[float] = None
    nearest_supermarket_km: Optional[float] = None
    nearest_gp_km: Optional[float] = None
    nearest_school_km: Optional[float] = None
    nearest_greenspace_km: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Meta(BaseModel):
    areas: int
    components: list[str]
    default_weights: dict[str, float]
    data_vintage: str
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
    local_typical_gbp: Optional[float] = None
    pct_vs_local: Optional[float] = None
    band: str
    basis: str


class ListingCheckResponse(BaseModel):
    postcode: str
    msoa_code: str
    msoa_name: Optional[str] = None
    area: Area
    price: Optional[PriceCheck] = None
