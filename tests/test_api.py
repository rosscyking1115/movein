"""Tests for the FastAPI service (no network — postcodes.io is mocked)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _an_area_code() -> str:
    return client.post("/v1/search", json={"limit": 1}).json()["results"][0]["area_id"]


class ApiTests(unittest.TestCase):
    def test_healthz(self) -> None:
        response = client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["areas"], 7000)

    def test_meta(self) -> None:
        response = client.get("/v1/meta")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["components"]), 5)

    def test_area_lookup_and_404(self) -> None:
        code = _an_area_code()
        ok = client.get(f"/v1/areas/{code}")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["area_id"], code)
        self.assertEqual(client.get("/v1/areas/NOTACODE").status_code, 404)

    def test_search_reranks_on_weights(self) -> None:
        safe = client.post("/v1/search", json={"weights": {"safety_score": 5}, "limit": 1}).json()["results"][0]
        conv = client.post("/v1/search", json={"weights": {"convenience_score": 5}, "limit": 1}).json()["results"][0]
        self.assertIsNotNone(safe["match_score"])
        self.assertNotEqual(safe["area_id"], conv["area_id"])

    def test_search_budget_filter(self) -> None:
        response = client.post("/v1/search", json={"max_rent": 700, "limit": 10})
        self.assertEqual(response.status_code, 200)
        for item in response.json()["results"]:
            rent = item["official_rent_monthly_gbp"]
            if rent is not None:
                self.assertLessEqual(rent, 700)

    def test_listing_check_rent(self) -> None:
        code = _an_area_code()
        fake = {"msoa_code": code, "msoa_name": "Test MSOA", "country": "England"}
        with patch("api.postcodes.resolve", return_value=fake):
            response = client.post(
                "/v1/listing-check",
                json={"postcode": "E1 6AN", "deal": "rent", "bedrooms": "2", "asking_gbp": 1500},
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["area"]["area_id"], code)
        self.assertIn("band", body["price"])

    def test_listing_check_outside_coverage(self) -> None:
        fake = {"msoa_code": "S02000001", "msoa_name": "Edinburgh", "country": "Scotland"}
        with patch("api.postcodes.resolve", return_value=fake):
            response = client.post("/v1/listing-check", json={"postcode": "EH1 1AA", "asking_gbp": 1000})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
