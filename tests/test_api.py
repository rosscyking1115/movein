"""Tests for the FastAPI service (no network — postcodes.io is mocked)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from api import data
from api.main import app

client = TestClient(app)


def _an_area_code() -> str:
    return client.post("/v2/search", json={"limit": 1}).json()["results"][0]["area_id"]


class ApiTests(unittest.TestCase):
    def test_record_cleaner_maps_missing_dates_to_null(self) -> None:
        self.assertIsNone(data.clean({"rent_reference_date": pd.NaT})["rent_reference_date"])

    def test_healthz(self) -> None:
        response = client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["areas"], 7000)

    def test_meta(self) -> None:
        response = client.get("/v2/meta")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["components"]), 5)
        self.assertEqual(response.json()["scoring_contract_version"], "2.0.0")

    def test_openapi_publishes_only_the_v2_contract(self) -> None:
        schema = client.get("/openapi.json").json()
        self.assertEqual(schema["info"]["title"], "England & Wales Housing Decision Support API")
        self.assertEqual(schema["info"]["version"], "2.0.0")
        self.assertIn("/v2/areas/{msoa_code}", schema["paths"])
        self.assertIn("/v2/listing-check", schema["paths"])
        self.assertFalse(any(path.startswith("/v1/") for path in schema["paths"]))
        price_schema = schema["components"]["schemas"]["PriceCheck"]["properties"]
        self.assertIn("comparison_gbp", price_schema)
        self.assertIn("pct_vs_comparison", price_schema)
        self.assertNotIn("local_typical_gbp", price_schema)
        self.assertNotIn("pct_vs_local", price_schema)

    def test_areas_index(self) -> None:
        response = client.get("/v2/areas/index")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreater(body["count"], 7000)
        self.assertEqual(body["count"], len(body["areas"]))
        self.assertIn("area_id", body["areas"][0])

    def test_area_lookup_and_404(self) -> None:
        code = _an_area_code()
        ok = client.get(f"/v2/areas/{code}")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["area_id"], code)
        self.assertIn(ok.json()["evidence_quality_level"], {"strong", "mixed", "limited"})
        self.assertEqual(client.get("/v2/areas/NOTACODE").status_code, 404)

    def test_search_reranks_on_weights(self) -> None:
        safe = client.post("/v2/search", json={"weights": {"safety_score": 5}, "limit": 1}).json()["results"][0]
        conv = client.post("/v2/search", json={"weights": {"convenience_score": 5}, "limit": 1}).json()["results"][0]
        self.assertIsNotNone(safe["match_score"])
        self.assertNotEqual(safe["area_id"], conv["area_id"])

    def test_search_budget_filter(self) -> None:
        response = client.post("/v2/search", json={"max_rent": 700, "limit": 10})
        self.assertEqual(response.status_code, 200)
        for item in response.json()["results"]:
            rent = item["official_rent_monthly_gbp"]
            if rent is not None:
                self.assertLessEqual(rent, 700)

    def test_search_rejects_unknown_or_out_of_range_weights(self) -> None:
        self.assertEqual(
            client.post("/v2/search", json={"weights": {"not_a_component": 1}}).status_code,
            422,
        )
        self.assertEqual(
            client.post("/v2/search", json={"weights": {"energy_score": 6}}).status_code,
            422,
        )

    def test_welsh_area_marks_england_only_sources_unknown(self) -> None:
        welsh = data.areas().loc[data.areas()["area_id"].str.startswith("W")].iloc[0]
        response = client.get(f"/v2/areas/{welsh['area_id']}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["flood_score"])
        self.assertEqual(body["flood_source_status"], "not_covered")
        self.assertEqual(body["planning_source_status"], "not_covered")
        self.assertEqual(body["evidence_quality_level"], "limited")

    def test_missing_crime_denominator_remains_unknown(self) -> None:
        code = _an_area_code()
        record = data.get_area(code)
        self.assertIsNotNone(record)
        record = dict(record or {})
        record.update(
            crime_population_denominator=None,
            crime_population_reference_date=None,
            crime_rate_per_1000=None,
            safety_score=None,
            evidence_quality_level="limited",
            evidence_quality_notes=(
                "Limited evidence: a compatible population denominator is unavailable "
                "for the crime indicator."
            ),
        )
        with patch("api.main.data.get_area", return_value=record):
            body = client.get(f"/v2/areas/{code}").json()
        self.assertIsNone(body["crime_population_denominator"])
        self.assertIsNone(body["crime_rate_per_1000"])
        self.assertIsNone(body["safety_score"])
        self.assertEqual(body["evidence_quality_level"], "limited")

    def test_listing_check_rent(self) -> None:
        code = _an_area_code()
        fake = {"msoa_code": code, "msoa_name": "Test MSOA", "country": "England"}
        with patch("api.postcodes.resolve", return_value=fake):
            response = client.post(
                "/v2/listing-check",
                json={"postcode": "E1 6AN", "deal": "rent", "bedrooms": "2", "asking_gbp": 1500},
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["area"]["area_id"], code)
        self.assertIn("band", body["price"])
        self.assertIn("comparison_gbp", body["price"])
        self.assertIn("pct_vs_comparison", body["price"])
        self.assertNotIn("local_typical_gbp", body["price"])
        self.assertNotIn("pct_vs_local", body["price"])
        self.assertIn("official local-authority 2-bed rent context for", body["price"]["basis"])
        self.assertEqual(body["area"]["rent_source_grain"], "local_authority")

    def test_v1_listing_check_retains_hidden_legacy_field_names(self) -> None:
        code = _an_area_code()
        fake = {"msoa_code": code, "msoa_name": "Test MSOA", "country": "England"}
        with patch("api.postcodes.resolve", return_value=fake):
            response = client.post(
                "/v1/listing-check",
                json={"postcode": "E1 6AN", "deal": "rent", "bedrooms": "2", "asking_gbp": 1500},
            )
        self.assertEqual(response.status_code, 200)
        price = response.json()["price"]
        self.assertIn("local_typical_gbp", price)
        self.assertIn("pct_vs_local", price)
        self.assertNotIn("comparison_gbp", price)
        self.assertNotIn("pct_vs_comparison", price)

    def test_listing_check_outside_coverage(self) -> None:
        fake = {"msoa_code": "S02000001", "msoa_name": "Edinburgh", "country": "Scotland"}
        with patch("api.postcodes.resolve", return_value=fake):
            response = client.post("/v2/listing-check", json={"postcode": "EH1 1AA", "asking_gbp": 1000})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
