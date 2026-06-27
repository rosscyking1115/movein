"""Unit tests for the ONSPD geography seed normalizer."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd

from scripts import prepare_onspd_seed


class PrepareOnspdSeedTests(unittest.TestCase):
    def test_normalizes_common_onspd_csv_columns(self) -> None:
        lookup = pd.DataFrame(
            [
                {
                    "pcds": "sw1p3an",
                    "msoa21": "E02000977",
                    "msoa21nm": "Westminster Millbank",
                    "lsoa21": "E01004736",
                    "oslaua": "E09000033",
                    "ladnm": "Westminster",
                    "rgn": "London",
                    "lat": "51.4975",
                    "long": "-0.1357",
                    "doterm": "",
                },
                {
                    "pcds": "ZZ999ZZ",
                    "msoa21": "E020_RETIRED",
                    "msoa21nm": "",
                    "lsoa21": "E010_RETIRED",
                    "oslaua": "E07000000",
                    "ladnm": "",
                    "rgn": "Unknown",
                    "lat": "51.5000",
                    "long": "-0.1000",
                    "doterm": "2024-01-01",
                },
            ]
        )

        normalized = prepare_onspd_seed.normalize_lookup(
            lookup,
            snapshot_date="2026-05-01",
            source_name="Fixture ONSPD",
            source_url="https://example.test/onspd",
        )

        self.assertEqual(list(normalized.columns), prepare_onspd_seed.CONTRACT_COLUMNS)
        active_row = normalized[normalized["postcode"] == "SW1P 3AN"].iloc[0]
        retired_row = normalized[normalized["postcode"] == "ZZ99 9ZZ"].iloc[0]

        self.assertEqual(active_row["postcode_outward"], "SW1P")
        self.assertEqual(active_row["postcode_area"], "SW")
        self.assertEqual(active_row["is_current_postcode"], "true")
        self.assertEqual(retired_row["is_current_postcode"], "false")
        self.assertEqual(retired_row["area_name"], "E020_RETIRED")
        self.assertEqual(retired_row["local_authority_name"], "E07000000")

    def test_prepare_seed_reads_zip_member_and_applies_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            zip_path = tmp_path / "onspd.zip"
            output_path = tmp_path / "normalized.csv"
            csv_text = (
                "pcd,msoa11,lsoa11,oslaua,lat,long\n"
                "AA11AA,E02000001,E01000001,E09000001,51.1,-0.1\n"
                "BB22BB,E02000002,E01000002,E09000002,52.2,-0.2\n"
            )
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("README.txt", "metadata")
                archive.writestr("Data/ONSPD_SAMPLE.csv", csv_text)

            result = prepare_onspd_seed.prepare_seed(
                zip_path,
                output_path,
                snapshot_date="2026-05-01",
                member="Data/*.csv",
                limit=1,
            )

            output = pd.read_csv(output_path, dtype=str)

        self.assertEqual(result.rows_written, 1)
        self.assertEqual(result.source_member, "Data/ONSPD_SAMPLE.csv")
        self.assertEqual(output.loc[0, "postcode"], "AA1 1AA")
        self.assertEqual(output.loc[0, "area_name"], "E02000001")
        self.assertEqual(output.loc[0, "local_authority_name"], "E09000001")

    def test_missing_required_column_raises_clear_error(self) -> None:
        lookup = pd.DataFrame(
            [
                {
                    "pcds": "AA1 1AA",
                    "lsoa21": "E01000001",
                    "oslaua": "E09000001",
                    "lat": "51.1",
                    "long": "-0.1",
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "area_id"):
            prepare_onspd_seed.normalize_lookup(
                lookup,
                snapshot_date="2026-05-01",
            )


if __name__ == "__main__":
    unittest.main()
