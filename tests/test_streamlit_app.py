"""Smoke tests for the renter decision app render tree."""

from __future__ import annotations

import logging
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").disabled = True


class RenterAppTests(unittest.TestCase):
    def run_app(self, relative_path: str) -> AppTest:
        app = AppTest.from_file(str(ROOT / relative_path))
        app.run(timeout=30)
        if app.exception:
            self.fail("\n".join(exc.message for exc in app.exception))
        return app

    def test_home_page_ranks_areas(self) -> None:
        app = self.run_app("app/streamlit_app.py")
        self.assertIn("Where to live", app.title[0].value)
        self.assertGreaterEqual(len(app.dataframe), 1)
        self.assertGreaterEqual(len(app.slider), 5)  # five priority weights

    def test_secondary_pages_render(self) -> None:
        for path, title in [
            ("app/pages/1_Compare_areas.py", "Compare areas"),
            ("app/pages/2_Sources_and_caveats.py", "Sources & caveats"),
            ("app/pages/3_Listing_checker.py", "Check a listing"),
        ]:
            with self.subTest(path=path):
                app = self.run_app(path)
                self.assertIn(title, app.title[0].value)


if __name__ == "__main__":
    unittest.main()
