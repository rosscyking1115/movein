"""Golden-case parity tests for the versioned scoring contract."""

from __future__ import annotations

import json
import csv
import unittest
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from api import scoring
from scripts import rescore_extract

ROOT = Path(__file__).resolve().parent.parent


class ScoringContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads((ROOT / "contracts/neighbourhood-scoring-v2.json").read_text())
        cls.cases = json.loads((ROOT / "contracts/neighbourhood-scoring-v2-cases.json").read_text())

    def test_api_uses_declared_contract_version_and_defaults(self) -> None:
        self.assertEqual(scoring.CONTRACT_VERSION, self.contract["schema_version"])
        expected = {
            key: value["default_weight"]
            for key, value in self.contract["components"].items()
        }
        self.assertEqual(scoring.DEFAULT_WEIGHTS, expected)

    def test_dbt_and_extract_defaults_match_the_contract(self) -> None:
        project = yaml.safe_load((ROOT / "dbt_project.yml").read_text())
        self.assertEqual(
            float(project["vars"]["score_weight_min"]),
            float(self.contract["allowed_weight"]["minimum"]),
        )
        self.assertEqual(
            float(project["vars"]["score_weight_max"]),
            float(self.contract["allowed_weight"]["maximum"]),
        )
        dbt_weights = {
            component: float(project["vars"][f"score_weight_{component.removesuffix('_score')}"])
            for component in self.contract["components"]
        }
        expected = {
            component: float(config["default_weight"])
            for component, config in self.contract["components"].items()
        }
        self.assertEqual(dbt_weights, expected)
        self.assertEqual(
            rescore_extract.WEIGHTS,
            {key.removesuffix("_score"): value for key, value in expected.items()},
        )

    def test_rescore_sql_matches_the_committed_extract(self) -> None:
        db_path = ROOT / "data" / "decision.duckdb"
        with duckdb.connect(str(db_path), read_only=True) as connection:
            expected = connection.execute(
                "select * from app.rpt_neighbourhood_score order by area_id"
            ).df()
            actual = connection.execute(
                f"select * from ({rescore_extract.SCORE_SQL}) scored order by area_id"
            ).df()
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False)

    def test_python_reweight_matches_every_golden_case(self) -> None:
        for case in self.cases["cases"]:
            with self.subTest(case=case["name"]):
                ranked = scoring.reweight(
                    pd.DataFrame([{"area_id": "TEST", **case["scores"]}]),
                    case["weights"],
                )
                actual = ranked.iloc[0]["match_score"]
                expected = case["expected"]
                if expected is None:
                    self.assertTrue(pd.isna(actual))
                else:
                    self.assertEqual(actual, expected)

    def test_python_evidence_quality_matches_every_golden_case(self) -> None:
        for case in self.cases["evidence_cases"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(scoring.evidence_quality(**case["inputs"]), case["expected"])

    def test_python_ranking_uses_contract_tie_order(self) -> None:
        self.assertEqual(self.contract["tie_order"], ["score_desc", "area_id_asc"])
        for case in self.cases["ranking_cases"]:
            frame = pd.DataFrame(
                [
                    {
                        "area_id": item["area_id"],
                        **{component: item["score"] for component in scoring.COMPONENTS},
                    }
                    for item in case["areas"]
                ]
            )
            ranked = scoring.reweight(frame, scoring.DEFAULT_WEIGHTS)
            self.assertEqual(ranked["area_id"].tolist(), case["expected_area_ids"])

    def test_dbt_scoring_seed_mirrors_json_cases(self) -> None:
        with (ROOT / "seeds/ref_scoring_golden_cases.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([row["case_name"] for row in rows], [case["name"] for case in self.cases["cases"]])

        for row, case in zip(rows, self.cases["cases"], strict=True):
            for component in scoring.COMPONENTS:
                csv_score = None if row[component] == "" else float(row[component])
                self.assertEqual(csv_score, case["scores"][component])
                expected_weight = float(case["weights"].get(component, 1.0))
                self.assertEqual(float(row[component.replace("_score", "_weight")]), expected_weight)
            csv_expected = None if row["expected_score"] == "" else float(row["expected_score"])
            self.assertEqual(csv_expected, case["expected"])

    def test_dbt_ranking_seed_mirrors_json_cases(self) -> None:
        with (ROOT / "seeds/ref_ranking_golden_cases.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))

        expected_rows = []
        for case in self.cases["ranking_cases"]:
            expected_positions = {
                area_id: position
                for position, area_id in enumerate(case["expected_area_ids"], start=1)
            }
            expected_rows.extend(
                {
                    "case_name": case["name"],
                    "area_id": area["area_id"],
                    "score": float(area["score"]),
                    "expected_position": expected_positions[area["area_id"]],
                }
                for area in case["areas"]
            )

        actual_rows = [
            {
                "case_name": row["case_name"],
                "area_id": row["area_id"],
                "score": float(row["score"]),
                "expected_position": int(row["expected_position"]),
            }
            for row in rows
        ]
        self.assertEqual(actual_rows, expected_rows)

    def test_dbt_evidence_seed_mirrors_json_cases(self) -> None:
        with (ROOT / "seeds/ref_evidence_golden_cases.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(
            [row["case_name"] for row in rows],
            [case["name"] for case in self.cases["evidence_cases"]],
        )

        for row, case in zip(rows, self.cases["evidence_cases"], strict=True):
            inputs = case["inputs"]
            self.assertEqual(int(row["available_component_count"]), inputs["available_component_count"])
            denominator = row["crime_population_denominator"]
            self.assertEqual(None if denominator == "" else int(denominator), inputs["crime_population_denominator"])
            for key in (
                "crime_population_reference_date",
                "crime_period_start",
                "crime_period_end",
                "rent_source_grain",
                "rent_reference_date",
                "median_sale_price_confidence",
                "all_component_source_dates_known",
                "planning_source_status",
                "flood_source_status",
            ):
                if key == "all_component_source_dates_known":
                    self.assertEqual(row[key].lower() == "true", inputs[key])
                else:
                    self.assertEqual(row[key] or None, inputs[key])
            self.assertEqual(row["expected_level"], case["expected"])


if __name__ == "__main__":
    unittest.main()
