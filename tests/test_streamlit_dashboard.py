"""Smoke tests for the Streamlit dashboard render tree."""

from __future__ import annotations

import logging
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parent.parent
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").disabled = True


class StreamlitDashboardTests(unittest.TestCase):
    def run_app(self, relative_path: str) -> AppTest:
        app = AppTest.from_file(str(ROOT / relative_path))
        app.run(timeout=20)
        if app.exception:
            messages = "\n".join(exc.message for exc in app.exception)
            self.fail(messages)
        return app

    def test_home_page_renders_headline_metrics(self) -> None:
        app = self.run_app("dashboard/streamlit_app.py")

        self.assertIn("UK Property Analytics", app.title[0].value)
        self.assertEqual(len(app.metric), 3)

    def test_deep_dive_pages_render(self) -> None:
        cases = [
            ("dashboard/pages/1_Price_YoY_by_region.py", "Price YoY by region", 1),
            ("dashboard/pages/2_Top_postcode_areas.py", "Top postcode areas", 1),
            ("dashboard/pages/3_New_build_premium.py", "New-build premium", 1),
            ("dashboard/pages/4_About.py", "About this project", 0),
        ]

        for path, expected_title, min_dataframes in cases:
            with self.subTest(path=path):
                app = self.run_app(path)
                self.assertIn(expected_title, app.title[0].value)
                self.assertGreaterEqual(len(app.dataframe), min_dataframes)


if __name__ == "__main__":
    unittest.main()
