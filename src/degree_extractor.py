# src/degree_extractor.py

import re
from typing import List

def extract_degree_requirement(jd_text: str) -> List[str]:
    """
    Extract allowed degree levels from job description text.
    """
    text = jd_text.lower()
    degrees = []

    if re.search(r"\b(bachelor|b\.s\.|bs)\b", text):
        degrees.append("Bachelor")

    if re.search(r"\b(master|m\.s\.|ms)\b", text):
        degrees.append("Master")

    if re.search(r"\b(phd|doctorate)\b", text):
        degrees.append("PhD")

    return degrees
