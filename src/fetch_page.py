# src/fetch_page.py

from playwright.sync_api import sync_playwright
from html_extractor import extract_job_page_inputs


from playwright.sync_api import sync_playwright
from html_extractor import extract_job_page_inputs


def fetch_rendered_html(url: str, headless: bool = False) -> str:
    """
    Open a job page URL in a real browser and return fully rendered HTML.
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


if __name__ == "__main__":
    test_url = "https://www.linkedin.com/jobs/view/4348163604"

    html = fetch_rendered_html(url)
    info = extract_job_page_inputs(html)

    print("JOB TITLE:", info["job_title"])
    print("COMPANY:", info["company"])
    print("JD TEXT LENGTH:", len(info["jd_text"]))
