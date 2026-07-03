"""FastAPI service over the housing decision marts.

Serves the explainable area scores + facts, weighted search, postcode resolve,
and the listing price check. The same backend powers the website and mobile app.
Interactive docs at /docs. Indicators only — never a "safe/unsafe" verdict.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

logger = logging.getLogger("movein.coverage")

from . import data, postcodes, scoring
from .models import (
    Area,
    AreaIndexResponse,
    ListingCheckRequest,
    ListingCheckResponse,
    Meta,
    PriceCheck,
    ResolveResponse,
    SearchRequest,
    SearchResponse,
)

app = FastAPI(
    title="England & Wales Housing Decision Support API",
    version="1.0.0",
    description=(
        "Explainable neighbourhood (MSOA) scores for England & Wales, plus a "
        "postcode resolver and listing price check. Area-level indicators only — "
        "not a property valuation, never a safe/unsafe label. Scotland and "
        "Northern Ireland are on the roadmap, not yet covered."
    ),
)
# CORS allowlist from CORS_ALLOW_ORIGINS (comma-separated). Defaults to "*" for
# local dev; set it to the website origin(s) in production, e.g.
#   CORS_ALLOW_ORIGINS=https://www.example.com,https://example.com
_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _coverage_guard(location: dict | None) -> dict:
    if not location or not location.get("msoa_code"):
        raise HTTPException(status_code=404, detail="Postcode not found.")
    country = location.get("country")
    if country not in ("England", "Wales"):
        # Log out-of-coverage lookups (nation only — never the postcode) so demand
        # for Scotland/NI is visible and can steer what we build next.
        logger.info("out_of_coverage_lookup country=%s", country)
        raise HTTPException(
            status_code=422,
            detail=(
                f"We don't cover {country} yet — MoveIn is England & Wales for now, "
                "with Scotland and Northern Ireland on the roadmap."
            ),
        )
    record = data.get_area(location["msoa_code"])
    if record is None:
        raise HTTPException(status_code=404, detail="No area profile for that postcode yet.")
    return record


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok", "areas": len(data.areas()), "data_vintage": data.data_vintage()}


@app.get("/v1/meta", response_model=Meta, tags=["meta"])
def meta() -> Meta:
    return Meta(
        areas=len(data.areas()),
        components=scoring.COMPONENTS,
        default_weights=scoring.DEFAULT_WEIGHTS,
        data_vintage=data.data_vintage(),
        note="England & Wales MSOAs. Component scores are 0-100 percentile ranks; indicators only.",
    )


@app.get("/v1/areas/resolve", response_model=ResolveResponse, tags=["areas"])
def resolve_postcode(postcode: str = Query(..., min_length=5, description="UK postcode, e.g. SW1A 1AA")) -> ResolveResponse:
    location = postcodes.resolve(postcode)
    record = _coverage_guard(location)
    return ResolveResponse(
        postcode=postcode.upper().strip(),
        msoa_code=location["msoa_code"],
        msoa_name=location.get("msoa_name"),
        area=Area(**record),
    )


# Declared before /v1/areas/{msoa_code} so the literal path wins the match.
@app.get("/v1/areas/index", response_model=AreaIndexResponse, tags=["areas"])
def areas_index() -> AreaIndexResponse:
    records = [Area(**data.clean(record)) for record in data.areas().to_dict("records")]
    return AreaIndexResponse(
        count=len(records),
        data_vintage=data.data_vintage(),
        areas=records,
    )


@app.get("/v1/areas/{msoa_code}", response_model=Area, tags=["areas"])
def get_area(msoa_code: str) -> Area:
    record = data.get_area(msoa_code)
    if record is None:
        raise HTTPException(status_code=404, detail="MSOA not found.")
    return Area(**record)


@app.post("/v1/search", response_model=SearchResponse, tags=["areas"])
def search(request: SearchRequest) -> SearchResponse:
    frame = data.areas().copy()
    if request.max_rent is not None:
        frame = frame[
            frame["official_rent_monthly_gbp"].isna()
            | (frame["official_rent_monthly_gbp"] <= request.max_rent)
        ]
    if request.regions:
        frame = frame[frame["region"].isin(request.regions)]

    weights = request.weights or scoring.DEFAULT_WEIGHTS
    ranked = scoring.reweight(frame, weights)
    if request.min_overall is not None:
        ranked = ranked[ranked["match_score"] >= request.min_overall]

    total = len(ranked)
    page = ranked.iloc[request.offset : request.offset + request.limit]
    results = [Area(**data.clean(record)) for record in page.to_dict("records")]
    return SearchResponse(total=total, limit=request.limit, offset=request.offset, results=results)


@app.post("/v1/listing-check", response_model=ListingCheckResponse, tags=["listing"])
def listing_check(request: ListingCheckRequest) -> ListingCheckResponse:
    location = postcodes.resolve(request.postcode)
    record = _coverage_guard(location)

    if request.deal == "rent":
        local = record.get(scoring.RENT_BY_BEDS[request.bedrooms])
        bed_label = "average" if request.bedrooms == "any" else f"{request.bedrooms.replace('plus', '+')}-bed"
        basis = f"{bed_label} rent in {record.get('local_authority_name')}"
    else:
        local = record.get("median_sale_price_gbp")
        basis = f"median sold price in {record.get('area_name')}"

    pct, band = scoring.price_verdict(request.asking_gbp, local)
    price = PriceCheck(
        asking_gbp=request.asking_gbp,
        local_typical_gbp=local,
        pct_vs_local=pct,
        band=band,
        basis=basis,
    )
    return ListingCheckResponse(
        postcode=request.postcode.upper().strip(),
        msoa_code=location["msoa_code"],
        msoa_name=location.get("msoa_name"),
        area=Area(**record),
        price=price,
    )
