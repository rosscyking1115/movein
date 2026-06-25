"""Regression tests for dependency import compatibility."""

from __future__ import annotations

import subprocess
import sys
import unittest


class DependencyImportTests(unittest.TestCase):
    def test_requests_imports_without_dependency_warning(self) -> None:
        result = subprocess.run(
            [sys.executable, "-W", "error", "-c", "import requests"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stderr.strip() or result.stdout.strip(),
        )


if __name__ == "__main__":
    unittest.main()
