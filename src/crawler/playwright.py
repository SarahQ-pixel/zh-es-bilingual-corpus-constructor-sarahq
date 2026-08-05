import yaml
from playwright.sync_api import sync_playwright
from pathlib import Path
import hashlib
import subprocess
import sys
import os


def load_config():
    with open("config/crawler_config.yaml", "r") as f:
        return yaml.safe_load(f)


def ensure_playwright_browser():
    browser_path = os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH"
    )

    if browser_path is None:
        raise RuntimeError(
            "PLAYWRIGHT_BROWSERS_PATH is not initialized. "
            "Please import core.bootstrap first."
        )

    browser_path = Path(browser_path)

    if ((not browser_path.exists()) or not any(browser_path.iterdir())):
        print("[playwright] Chromium browser not found. Installing...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "playwright",
                "install",
                "chromium"
            ],
            check=True
        )
        print(
            "[playwright] Chromium installation finished."
        )


def render_page(url, output_dir, config=None):
    ensure_playwright_browser()

    if config is None:
        config = load_config()

    pw_config = config["playwright"]

    if not pw_config.get("enabled", True):
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = config["output"]["output_filename_prefix"] + hashlib.md5(url.encode()).hexdigest() + ".html"
    path = output_dir / filename

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=pw_config["headless"]
        )

        try:
            context = browser.new_context()
            page = context.new_page()

            page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in [
                    "image",
                    "media",
                    "font"
                ]
                else route.continue_()
            )

            response = page.goto(
                url,
                timeout=pw_config["timeout"],
                wait_until=pw_config["wait_until"]
            )

            if response is not None:
                if response.status >= 400:
                    raise RuntimeError(
                        f"Playwright HTTP Error {response.status}"
                    )
                
            title = page.title().lower()

            blocked_titles = [
                "403 forbidden",
                "access denied",
                "request blocked"
            ]

            if title in blocked_titles:
                raise RuntimeError(
                    f"Blocked page title: {title}"
                )

            html = page.content()

            if len(html) < 300:
                raise RuntimeError(
                    "Rendered page too small"
                )

            with path.open("w", encoding="utf-8") as f:
                f.write(html)

            browser.close()

            return {
                "url": url,
                "rendered_html_path": str(path)
            }
        finally:
            browser.close()