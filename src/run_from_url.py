# src/run_from_url.py

import json

from fetch_page import fetch_rendered_html
from html_extractor import extract_job_page_inputs
from run import analyze_jd   # 你已有的 analyzer（或对应文件名）


def analyze_job_from_url(url: str) -> dict:
    """
    Full pipeline:
    URL -> HTML -> (job_title, company, jd_text) -> analyzer -> final JSON
    """

    # 1. Fetch rendered HTML
    html = fetch_rendered_html(url, headless=False)

    # 2. Extract structured inputs from HTML
    page_inputs = extract_job_page_inputs(html)

    job_title = page_inputs["job_title"]
    company = page_inputs["company"]
    jd_text = page_inputs["jd_text"]   # 内部用，不输出

    # 3. Run existing JD analyzer
    analysis = analyze_jd(jd_text)

    # 4. Assemble final output (NO jd_text)
    final_output = {
        "job_title": job_title,
        "company": company,
        "seniority": analysis.get("seniority", ""),
        "degree_requirement": analysis.get("degree_requirement", []),
        "fields": analysis.get("fields", []),
        "required_skills": analysis.get("required_skills", []),
        "preferred_skills": analysis.get("preferred_skills", []),
    }

    return final_output


if __name__ == "__main__":
    test_url = "https://www.linkedin.com/jobs/view/4348163604"

    result = analyze_job_from_url(test_url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
