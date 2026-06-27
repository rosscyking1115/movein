"""Browser-level smoke test for the Streamlit dashboard."""

from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
import unittest
import warnings
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent


def find_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_http(url: str, timeout_seconds: int = 45) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001 - keep retrying until timeout.
            last_error = exc
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for {url}: {last_error}")


def assert_screenshot_not_blank(testcase: unittest.TestCase, screenshot: bytes) -> None:
    image = Image.open(BytesIO(screenshot)).convert("RGB")
    if hasattr(image, "get_flattened_data"):
        pixels = list(image.get_flattened_data())
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            pixels = list(image.getdata())
    total = image.width * image.height
    non_white = sum(
        1
        for red, green, blue in pixels
        if (red, green, blue) != (255, 255, 255)
    )
    unique_sample = len(set(pixels[:: max(1, total // 5000)]))

    testcase.assertGreater(non_white / total, 0.02)
    testcase.assertGreater(unique_sample, 20)


class StreamlitBrowserTests(unittest.TestCase):
    def test_home_page_renders_in_browser_and_is_not_blank(self) -> None:
        port = find_free_port()
        url = f"http://127.0.0.1:{port}"

        log_file = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        log_path = Path(log_file.name)
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(ROOT / "dashboard" / "streamlit_app.py"),
                "--server.address",
                "127.0.0.1",
                "--server.port",
                str(port),
                "--server.headless",
                "true",
                "--server.fileWatcherType",
                "none",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        try:
            wait_for_http(url)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page(viewport={"width": 1440, "height": 1000})
                    page.goto(url, wait_until="networkidle", timeout=30_000)
                    page.get_by_text("UK Property Analytics").first.wait_for(
                        timeout=20_000
                    )
                    page.get_by_text("Headline metrics").first.wait_for(
                        timeout=20_000
                    )
                    page.get_by_text(
                        "Where in England & Wales has housing got more or less affordable?"
                    ).first.wait_for(timeout=20_000)
                    body_text = page.locator("body").inner_text()
                    self.assertIn("Three business questions", body_text)
                    screenshot = page.screenshot(full_page=True)
                finally:
                    browser.close()

            assert_screenshot_not_blank(self, screenshot)
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            log_file.close()

        if process.returncode not in {0, -15, 1}:
            self.fail(log_path.read_text(encoding="utf-8", errors="replace"))

        with suppress(OSError):
            log_path.unlink()


if __name__ == "__main__":
    unittest.main()
