# src/title_company_extractor.py

# src/title_company_extractor.py

import re
from typing import Tuple

JOB_KEYWORDS = [
    "intern",
    "engineer",
    "scientist",
    "analyst",
    "developer",
    "manager"
]

BOILERPLATE_KEYWORDS = [
    "about",
    "who we are",
    "the team",
    "who are you",
    "what you'll do",
    "what you will do"
]

def extract_job_title_and_company(jd_text: str) -> Tuple[str, str]:
    """
    Extract job title and company name from job description text,
    skipping LinkedIn boilerplate sections.
    """
    job_title = ""
    company = ""

    if not jd_text:
        return job_title, company

    lines = [line.strip() for line in jd_text.split("\n") if line.strip()]

    title_line = None
    for line in lines[:15]:  # 只在前 15 行找
        lower_line = line.lower()

        # 跳过模板行
        if any(bk in lower_line for bk in BOILERPLATE_KEYWORDS):
            continue

        # 必须包含职位关键词
        if any(jk in lower_line for jk in JOB_KEYWORDS):
            title_line = line
            break

    if title_line:
        # 从 title 行截断 at / , / .
        match = re.match(r"^(.*?)(?:\s+at\s+|,|\.)", title_line, re.IGNORECASE)
        if match:
            job_title = match.group(1).strip()
        else:
            job_title = title_line.strip()

        # company
        company_match = re.search(
            r"\bat\s+([A-Z][A-Za-z0-9&\-\s]+)",
            title_line
        )
        if company_match:
            company = company_match.group(1).strip()

    return job_title, company
