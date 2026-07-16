"""Regression tests for the ONS MSOA population seed normalizer."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts import prepare_msoa_population


class PrepareMsoaPopulationTests(unittest.TestCase):
    def test_normalizes_mid_2024_ons_workbook_sheet(self) -> None:
        source = pd.DataFrame(
            [
                {
                    "MSOA 2021 Code": "E02002483",
                    "MSOA 2021 Name": "Sample England",
                    "Total": "10,705",
                },
                {
                    "MSOA 2021 Code": "W02000422",
                    "MSOA 2021 Name": "Sample Wales",
                    "Total": 8123,
                },
            ]
        )

        result = prepare_msoa_population.normalize_population(source)

        self.assertEqual(list(result.columns), prepare_msoa_population.CONTRACT_COLUMNS)
        self.assertEqual(result["area_id"].tolist(), ["E02002483", "W02000422"])
        self.assertEqual(result["population"].tolist(), [10705, 8123])
        self.assertEqual(set(result["population_reference_date"]), {"2024-06-30"})
        self.assertEqual(set(result["geography_version"]), {"MSOA 2021"})

    def test_rejects_duplicate_or_non_positive_population(self) -> None:
        duplicate = pd.DataFrame(
            [
                {"MSOA 2021 Code": "E02000001", "MSOA 2021 Name": "A", "Total": 1},
                {"MSOA 2021 Code": "E02000001", "MSOA 2021 Name": "A", "Total": 0},
            ]
        )

        with self.assertRaisesRegex(ValueError, "unique positive"):
            prepare_msoa_population.normalize_population(duplicate)

    def test_prepare_writes_normalized_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook = Path(tmpdir) / "population.xlsx"
            output = Path(tmpdir) / "population.csv"
            frame = pd.DataFrame(
                [{"MSOA 2021 Code": "E02000001", "MSOA 2021 Name": "A", "Total": 7000}]
            )
            with pd.ExcelWriter(workbook) as writer:
                frame.to_excel(writer, sheet_name="Mid-2024 MSOA 2021", index=False, startrow=3)

            rows = prepare_msoa_population.prepare(workbook, output)
            written = pd.read_csv(output)

        self.assertEqual(rows, 1)
        self.assertEqual(written.loc[0, "population"], 7000)


if __name__ == "__main__":
    unittest.main()
