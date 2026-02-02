import re

def clean_jd_text(raw_text: str) -> str:
    """
    Clean raw job description text for downstream processing.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()
    text = re.sub(r"\s+", " ", text)

    return text
