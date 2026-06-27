"""Resolve a UK postcode to an MSOA via the free postcodes.io API (no key).

Used by the resolve and listing-check endpoints. Cached in-process; results are
never persisted. Kept tiny and side-effect-free so tests can monkeypatch it.
"""

from __future__ import annotations

from functools import lru_cache

import requests

_BASE = "https://api.postcodes.io/postcodes"


@lru_cache(maxsize=8192)
def resolve(postcode: str) -> dict | None:
    """Return {msoa_code, msoa_name, country} or None on any failure."""
    compact = "".join(postcode.split()).upper()
    if not compact:
        return None
    try:
        resp = requests.get(f"{_BASE}/{compact}", timeout=8)
        if resp.status_code != 200:
            return None
        result = resp.json().get("result") or {}
        return {
            "msoa_code": (result.get("codes") or {}).get("msoa"),
            "msoa_name": result.get("msoa"),
            "country": result.get("country"),
        }
    except requests.RequestException:
        return None
