"""Coverage semantics for England-only planning and flood sources."""

from __future__ import annotations

import unittest

from scripts.prepare_area_constraints import source_available, source_status


class ConstraintCoverageTests(unittest.TestCase):
    def test_wales_is_not_covered_even_when_source_file_exists(self) -> None:
        self.assertEqual(source_status("W02000422", source_available=True), "not_covered")

    def test_missing_source_is_not_reported_as_covered(self) -> None:
        self.assertEqual(source_status("E02000001", source_available=False), "source_missing")

    def test_england_is_covered_when_source_file_exists(self) -> None:
        self.assertEqual(source_status("E02000001", source_available=True), "covered")

    def test_empty_or_corrupt_snapshot_does_not_prove_coverage(self) -> None:
        self.assertFalse(source_available(0))
        self.assertTrue(source_available(1))
        self.assertEqual(
            source_status("E02000001", source_available=source_available(0)),
            "source_missing",
        )


if __name__ == "__main__":
    unittest.main()
