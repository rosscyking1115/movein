"""Unit tests for the Land Registry downloader control flow."""

from __future__ import annotations

import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import requests

from scripts import download_raw


class DownloadRawTests(unittest.TestCase):
    def test_default_years_come_from_dbt_project_vars(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "dbt_project.yml"
            config_path.write_text(
                """
name: test_project
vars:
  landreg_start_year: 2022
  landreg_end_year: 2024
models:
  test_project: {}
""",
                encoding="utf-8",
            )

            years = download_raw.select_years(
                Namespace(sample=False, years=None),
                config_path=config_path,
            )

            self.assertEqual(years, [2022, 2023, 2024])

    def test_sample_uses_latest_two_configured_years(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "dbt_project.yml"
            config_path.write_text(
                """
name: test_project
vars:
  landreg_start_year: 2022
  landreg_end_year: 2024
models:
  test_project: {}
""",
                encoding="utf-8",
            )

            years = download_raw.select_years(
                Namespace(sample=True, years=None),
                config_path=config_path,
            )

            self.assertEqual(years, [2023, 2024])

    def test_explicit_years_do_not_require_config_file(self) -> None:
        missing_config = Path("does-not-exist.yml")

        years = download_raw.select_years(
            Namespace(sample=False, years=[2025, 2024, 2025]),
            config_path=missing_config,
        )

        self.assertEqual(years, [2024, 2025])

    def test_existing_parquet_skips_network_without_force_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir)
            parquet_path = raw_dir / "pp-2099.parquet"
            parquet_path.write_bytes(b"existing")

            with (
                patch.object(download_raw, "RAW_DIR", raw_dir),
                patch.object(download_raw.requests, "get") as get,
            ):
                result = download_raw.download_year(2099)

            self.assertEqual(result, parquet_path)
            get.assert_not_called()
            self.assertEqual(parquet_path.read_bytes(), b"existing")

    def test_force_refresh_keeps_existing_parquet_when_download_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir)
            parquet_path = raw_dir / "pp-2099.parquet"
            parquet_path.write_bytes(b"existing")

            with (
                patch.object(download_raw, "RAW_DIR", raw_dir),
                patch.object(
                    download_raw.requests,
                    "get",
                    side_effect=requests.ConnectionError("network down"),
                ),
            ):
                with self.assertRaises(requests.ConnectionError):
                    download_raw.download_year(2099, force_refresh=True)

            self.assertEqual(parquet_path.read_bytes(), b"existing")
            self.assertFalse((raw_dir / "pp-2099.parquet.tmp").exists())


if __name__ == "__main__":
    unittest.main()
