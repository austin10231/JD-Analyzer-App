# src/fetch_page.py

from playwright.sync_api import sync_playwright
from html_extractor import extract_job_page_inputs


def fetch_rendered_html(url: str, headless: bool = True) -> str:
    """
    Fetch a job posting URL using Playwright (headless) and return fully rendered HTML.

    IMPORTANT:
    - Always headless=True in web applications
    - Never open a real browser window from Flask
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        html = page.content()

        browser.close()
        return html

